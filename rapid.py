import sublime, sublime_plugin
import socket
import time
import threading
import os
import subprocess
import re

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings
from .rapid_utils import parse_debug_message

# to run execute from the console:
# view.run_command('rapid_eval')

class RapidConnectionThread(threading.Thread):
	instance = None
	
	def __init__(self):
		self.host = "localhost"
		settings = RapidSettings().getSettings()
		if "Host" in settings:
			self.host = settings["Host"]

		self.port = 4444
		self.sock = None
		self.running = False

		try:
			threading.Thread.__init__(self)
			self.sock = socket.create_connection((self.host, self.port))
			#RapidOutputView.printMessage("Connected to " + self.host + ".")
			RapidConnectionThread.instance = self
		except OSError as e:
			RapidOutputView.printMessage("Failed to connect to rapid server:\n" + str(e) + "\n")


	def run(self):
		self.running = True

		try:
			self.readFromSocket()
		finally:
			self.sock.close()
			self.running = False
			del self.sock
			RapidOutputView.printMessage("Connection terminated")


	def readFromSocket(self):
		dataQueue = []

		while True:
			try:
				data = self.sock.recv(1)
			except socket.error:
				RapidOutputView.printMessage("Socket error")
				break

			data = self.decodeData(data)

			if not data:
				break

			if data != '\000':
				dataQueue.append(data)

			if data == '\n' or data == '\000':
				if dataQueue: #dataQueue is not empty
					datastr = "".join(dataQueue)
					self.receiveString(datastr)
				del dataQueue[:]


	def decodeData(self, data):
		#avoid error if received data is non-ascii (print space instead)
		try:
			return data.decode()
		except UnicodeDecodeError:
			return " "


	def isRunning(self):
		return self.running


	def receiveString(self, msg):
		# called when a string is received from the app
		#print("received: " + msg)

		# process debug commands
		if msg.startswith("#"):
			success, err = parse_debug_message(msg)

			if not success:
				RapidOutputView.printMessage(err)

		RapidOutputView.printMessage(msg)


	def _sendString(self, msg):
		#ignore non-ascii characters when sending
		#msg = msg.encode('ascii', 'ignore')
		#print("Sending:")
		#print(msg)
		self.sock.send(msg.encode())


	@staticmethod
	def sendString(msg):
		RapidConnectionThread.checkConnection()
		RapidConnectionThread.instance._sendString(msg + '\000')


	@staticmethod
	def checkConnection():
		if RapidConnectionThread.instance == None:
			RapidConnect()
			RapidConnectionThread().start()
		elif not RapidConnectionThread.instance.isRunning():
			RapidConnectionThread.instance.join()
			RapidConnect()
			RapidConnectionThread().start()

class RapidResumeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.sendString("\nsys.resume()")

class RapidHelpCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		cursor_pos = self.view.sel()[0].begin()
		region = self.view.word(cursor_pos)
		word = self.view.substr(region)
		#print("Sending word: " + word)
		line = "\nrequire(\"doc\"); doc.find([["+ word +"]])"
		RapidConnectionThread.sendString(line)

class RapidEvalCommand(sublime_plugin.TextCommand):
	def run(self, edit):

		#do not evaluate python files
		if self.view.file_name() != None and self.view.file_name().endswith("py"):
			print("cannot evaluate python files")
			return

		line_contents = self.getLines()
		RapidConnectionThread.sendString(line_contents)


	# Checks if the cursor is inside lua function() block
	def checkBlock(self, view, current_row, line_contents, cursor_pos):
		#added special case check for comments inside a block which might have no indentation
		ilevel = self.view.indentation_level(cursor_pos)
		if ilevel > 0 or (ilevel == 0 and line_contents.startswith("--")):
			return True
		elif line_contents.strip() == '':
			# cursor might be on an empty unintended row inside block
			start_row = current_row
			end_row = current_row
			index = 1

			# find first previous non-empty row
			while True:
				start_row = current_row - index
				start_pos = self.view.text_point(start_row, 0)
				start_line = self.view.full_line(start_pos)
				start_line_contents = self.view.substr(start_line)
				if start_line_contents.strip() != '':
					break
				else:
					index = index + 1

			#find first next non-empty row
			index = 1
			last_pos = -1
			while True:
				end_row = current_row + index
				end_pos = self.view.text_point(end_row, 0)
				end_line = self.view.full_line(end_pos)
				end_line_contents = self.view.substr(end_line)
				if last_pos == end_pos or end_line_contents.strip() != '':
					break
				else:
					index = index + 1
				last_pos = end_pos

			# Assume that the cursor is inside a function block if:
			# 1) start_row and end_row have indentation level > 0 OR
			# 2) start_row has indentation level > 0 and end_row starts with "end" OR
			# 3) start_row starts with "function" or "local function" and end_row indentation level > 0
			if (self.view.indentation_level(start_pos) > 0 and self.view.indentation_level(end_pos) > 0):
				return True
			elif (self.view.indentation_level(start_pos) > 0 \
				and self.view.indentation_level(end_pos) == 0 and end_line_contents.startswith("end")):
				return True
			elif (self.view.indentation_level(start_pos) == 0 and self.view.indentation_level(end_pos) > 0) \
				and (start_line_contents.startswith("function") or start_line_contents.startswith("local function")):
				return True
			else:
				return False
		else:
			return False


	def getLines(self):
		for region in self.view.sel():
			cursor_pos = self.view.sel()[0].begin()
			current_row = self.view.rowcol(cursor_pos)[0]

			if region.empty():
				#check if we are evaluating a block instead of line
				line = self.view.full_line(region)
				line_contents = self.view.substr(line)
				
				# if self.view.indentation_level(cursor_pos) > 0 \
				# or ( self.view.indentation_level(cursor_pos) == 0 \
				# and line_contents.startswith("--") ):

				#eval block
				if self.checkBlock(self.view, current_row, line_contents, cursor_pos) == True:
					start_row = current_row
					end_row = current_row
					index = 1

					#find start of the block
					block_start = False
					while not block_start:
						start_row = current_row - index
						start_pos = self.view.text_point(start_row, 0)
						start_line = self.view.full_line(start_pos)
						start_line_contents = self.view.substr(start_line)
						if self.view.indentation_level(start_pos) == 0 \
						and	start_line_contents.strip() != '' \
						and	not start_line_contents.startswith("--"):
							block_start = True
						else:
							index = index + 1

					#find end of the block
					index = 1
					block_end = False
					last_pos = -1
					while True:
						end_row = current_row + index
						end_pos = self.view.text_point(end_row, 0)
						if end_pos == last_pos:
							break
						last_pos = end_pos
						end_line = self.view.full_line(end_pos)
						end_line_contents = self.view.substr(end_line)
						if self.view.indentation_level(end_pos) == 0:
							if end_line_contents.strip() != '':
								if not end_line_contents.startswith("--"):
									break
						else:
							index = index + 1
					
					start_offset = self.view.text_point(start_row, 0)
					end_offset = self.view.text_point(end_row+1, 0)
					block_region = sublime.Region(start_offset, end_offset)
					line = self.view.full_line(block_region)

					file_row = start_row
					#print("Sending: " + str(file_row))
					msg = "Updating " + start_line_contents
					RapidOutputView.printMessage(msg)
					file_row_str = str(file_row + 1)
				else:
					line = self.view.line(region) #expand the region for full line if no selection
					file_row_str = str(current_row + 1)
			else:
				line = region #get only the selected area
				file_row_str = str(current_row + 1)

			file_name = self.view.file_name() or ""
			
			if len(file_name) > 0:
				# we always want to send only relative paths if possible, so
				# try to convert the filename to a relative path
				for window in sublime.windows():
					for folder in window.folders():
						if file_name.startswith(folder):
							file_name = os.path.relpath(file_name, folder)

			# replace possible backslashes with forward ones
			file_name = file_name.replace("\\", "/")

			line_str = self.view.substr(line)
			line_contents = "@" + file_name + ":" + file_row_str + "\n" + line_str
			
			#print("------")
			#print("Sending: ", file_name)
			#print("Sending contents:")
			#print(line_contents)
			#print("------")
			return line_contents


class RapidCheckServerAndStartupProjectCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.view = self.window.active_view()
		self.view.run_command('rapid_output_view_clear')

		#Check if startup project exists and if it has been modified
		startup_exists = False
		is_modified = False

		#RapidOutputView.printMessage("Loading project settings...")
		startup_path = RapidSettings().getStartupFilePath()
		RapidOutputView.printMessage("Startup path: " + startup_path)

		if startup_path:
			startup_exists = True
			new_view = sublime.active_window().find_open_file(startup_path)
			if new_view != None and new_view.is_dirty():
				is_modified = True
		elif self.view.is_dirty():
			is_modified = True

		#Send commands to server accordingly
		if startup_exists:
			#always load project, even if it is open and modified (modifications are loaded only after saving)
			RapidOutputView.printMessage("Startup project: " + startup_path)
			line = "\nsys.loadProject([[" + startup_path + "]])"
			RapidConnectionThread.sendString(line)
		else:
			#if no startup project, run current page
			if is_modified:
				#file has not been saved - restart runtime engine and send code over
				RapidConnectionThread.sendString("\nsys.restart()")
				line = "@" + self.view.file_name() + ":1\n" + self.view.substr(sublime.Region(0, self.view.size()))
				RapidConnectionThread.sendString(line)
			else:
				#file is up to date -> reload file - this is faster than sending the code
				RapidConnectionThread.sendString("\nsys.loadProject([[" + self.view.file_name() + "]])")


class RapidConnect():
	def __init__(self):
	
		#print("rapidconnect")

		#rapid_exe = sublime.active_window().active_view().settings().get("RapidExe")
		settings = RapidSettings().getSettings()
		rapid_exe = settings["RapidExe"]

		if os.name == "nt":
			# check if rapid is already running	
			rapid_running = True
			rapid = subprocess.check_output("tasklist /FI \"IMAGENAME eq " + rapid_exe + ".exe\" /FO CSV")
			rapid_search = re.search(rapid_exe + ".exe", rapid.decode("ISO-8859-1"))
			if rapid_search == None:
				rapid_debug = subprocess.check_output("tasklist /FI \"IMAGENAME eq " + rapid_exe + "_d.exe\" /FO CSV")
				rapid_debug_search = re.search(rapid_exe + "_d.exe", rapid_debug.decode("ISO-8859-1"))
				if rapid_debug_search == None:
					rapid_running = False
			if rapid_running:
				return	
		elif os.name == "posix":
			data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
			rapid_running = False
			for line in data:
				lineStr = line.decode("utf-8")
				if lineStr.find(rapid_exe) > -1 and lineStr.find(os.getlogin()) > -1:
					print("Rapid executable is already running for user: " + os.getlogin())
					print(lineStr)
					rapid_running = True
					break
			if rapid_running:
				return

		if "Host" in settings and settings["Host"] != "localhost":
			return

		if os.name == "nt":
			rapid_path = settings["RapidPathWin"]
		elif os.name == "posix":
			os.chdir(RapidSettings().getStartupProjectPath()) 
			rapid_path = os.path.realpath(settings["RapidPathOSX"])
		else:
			RapidOutputView.printMessage("Could not find \"RapidPath<OS>\" variable from projects' rapid_sublime -file!")
			return

		if rapid_path != None and rapid_exe != None:
			RapidOutputView.printMessage("Starting " + rapid_exe)
			full_path = os.path.abspath(os.path.join(rapid_path, rapid_exe))
			subprocess.Popen(full_path, cwd=rapid_path)
			if os.name == "posix":
				time.sleep(0.5) #small delay to get server running on OSX
		else:
			RapidOutputView.printMessage("Could not start server executable!")
			RapidOutputView.printMessage("\"RapidPath<OS>\" and/or \"RapidExe\" variables not found from \"Preferences.sublime_settings\" file!")


class RapidTestCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
		#print(data)
		rapid_running = False
		for line in data:
			lineStr = line.decode("utf-8")
			if lineStr.find("rapid") > -1:
				rapid_running = True
				break
		if rapid_running:
			print("rapid is already running!")
		else:
			print("rapid is not running!")


# TODO figure out how to move this to a separate file
class RapidRestartGameFromRoomCommand(sublime_plugin.TextCommand):
	def run(self, edit):

		filename = get_filename(self.view)

		if filename == None:
			RapidOutputView.printMessage("The file has not been saved -> could not determine world.")
			return

		# TODO evaluate only lua files
		for region in self.view.sel():
			room_name = self.find_room_name(region)
			level_name = parse_room_filename(filename)

			if level_name != None and room_name != None:
				cmd = '@:1\nrestart_game("{0}","{1}");shb_bring_to_front(g.window);'
				RapidConnectionThread.sendString(cmd.format(level_name, room_name))
			else: 
				if level_name == None:
					RapidOutputView.printMessage("The path does not follow convention /levels/level.lua -> could not determine level name.")
				elif level_name == None:
					RapidOutputView.printMessage("No name=\"...\" found from selection -> could not determine room name.")

	def find_room_name(self, region):
		if region.empty():
			return self.find_room_name_from_cursor(region.begin())
		else:
			return self.find_room_name_from_selection(region)

	def find_room_name_from_selection(self, region):
		# a block selection: find the name inside the selection.
		lines = self.view.substr(region)
		m = re.search(r"""name\s*=\s*["'](\w+)["']""", lines)

		if m != None: return m.group(1)

	def find_room_name_from_cursor(self, point):
		# take current row
		row,_ = self.view.rowcol(point)

		# advance backwards until def_room is found
		while row >= 0:
			reg_line = self.view.full_line(self.view.text_point(row, 0))
			line = self.view.substr(reg_line)
			m = re.search(r"def_room[{\n\s]", line)
			if m != None: break

			# proceed to previous line
			row = row - 1

		# bail out if the def_room was not found
		if row < 0: return None

		# find a region where the name must be found by advancing forward and counting braces until a balance is achieved
		start_point = self.view.text_point(row, 0)
		current_point = start_point

		left = 0
		right = 0

		while current_point < self.view.size():
			# HACK: Of course, this does get fooled by e.g. braces in comments and strings. It is not a parser.
			current = self.view.substr(current_point)
			if current == '{': left += 1
			if current == '}': right += 1
			if left > 0 and left == right: break

			current_point = current_point + 1

		# find name pattern from the region defined by def_room and ending brace
		lines = self.view.substr(sublime.Region(start_point, current_point))
		m = re.search(r"""name\s*=\s*["'](\w+)["']""", lines)

		if m != None: return m.group(1)


def parse_room_filename(filename):
	return filename.replace("\\", "/").replace(".lua", ".level")

# this is a wrapper for extract and override:
def get_filename(view): return view.file_name()