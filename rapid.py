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
		# This is a lot faster than "localhost" on Windows
		self.host = "127.0.0.1"

		self.settings = RapidSettings()
		values = self.settings.getSettings()
		if "Host" in values:
			self.host = values["Host"]

		self.port = 4444
		self.sock = None
		self.running = False
		self.connected = False
		self.connectionFailureReported = False
		self.shouldExit = False
		self.reconnectIntervalInSeconds = 1.0

		threading.Thread.__init__(self)
		RapidConnectionThread.instance = self

		# If 'autoConnect' is True we try to connect to server repeatedly
		# If' autoConnect' is False, we assume we have successfully launched server executable ourselves and attempt to connect only once
		if not self.settings.isAutoConnectEnabled():
			self.connect()

	def connect(self):
		if self.connected:
			return

		try:
			print("Rapid: connecting at %d..." % time.time())
			self.sock = socket.create_connection((self.host, self.port))
			RapidOutputView.printMessage("Connected to server at %s:%d." % (self.host, self.port))
			self.connected = True

			# re-enable error messages if they happen to be suppressed
			self.connectionFailureReported = False
		except OSError as e:
			self.connected = False
			if not self.connectionFailureReported:
				RapidOutputView.printMessage("Failed to connect to server:\n" + str(e) + "\n")
				# Suppress further print-outs
				self.connectionFailureReported = True

	def run(self):
		self.running = True

		if self.settings.isAutoConnectEnabled():
			# Auto-connect on
			while not self.shouldExit:
				if not self.connected:
					self.connect()
					if not self.connected:
						time.sleep(self.reconnectIntervalInSeconds)
				else:
					try:
						self.readFromSocket()
					finally:
						self.sock.close()
						self.connected = False
						del self.sock
						RapidOutputView.printMessage("Connection terminated")

						# Suppress connection errors from now on; this was deemed confusing. We did already report about the
						# connection error, didn't we? AutoConnect option makes no difference here, because regardless of
						# the value, when sending a message to the server, the suppression is removed.
						self.connectionFailureReported = True
		else:
			# Auto-connect off
			try:
				self.readFromSocket()
			finally:
				self.sock.close()
				self.running = False
				del self.sock
				RapidOutputView.printMessage("Connection terminated")

		self.running = False

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
		# Enable failure reporting here; we want feedback when explicitly sending messages to the server
		RapidConnectionThread.instance.connectionFailureReported = False

		if RapidConnectionThread.instance.connected:
			RapidConnectionThread.instance._sendString(msg + '\000')
		else:
			print("sendString failed - not connected!")

	@staticmethod
	def checkConnection():
		instance = RapidConnectionThread.instance

		if instance == None:
			RapidStartExecutable()
			RapidConnectionThread().start()
		elif not instance.running:
			# JS: when do we actually end up here?
			instance.join()
			RapidStartExecutable()
			RapidConnectionThread().start()

	@staticmethod
	def killConnection():
		instance = RapidConnectionThread.instance
		RapidConnectionThread.instance = None

		if instance == None or not instance.running:
			return

		instance.shouldExit = True

		# closing the socket aborts the thread
		instance.sock.close()

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
				if start_row < 0:
					start_row = 0
				start_pos = self.view.text_point(start_row, 0)
				start_line = self.view.full_line(start_pos)
				start_line_contents = self.view.substr(start_line)
				if start_row == 0 or start_line_contents.strip() != '':
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
					while True:
						start_row = current_row - index
						if start_row < 0:
							start_row = 0
						start_pos = self.view.text_point(start_row, 0)
						start_line = self.view.full_line(start_pos)
						start_line_contents = self.view.substr(start_line)
						if start_row == 0:
							break
						if self.view.indentation_level(start_pos) == 0 \
						and start_line_contents.strip() != '' \
						and not start_line_contents.startswith("--"):
							break
						else:
							index = index + 1

					#find end of the block
					index = 1
					last_pos = -1
					while True:
						end_row = current_row + index
						end_pos = self.view.text_point(end_row, 0)
						if end_pos == last_pos:
							break
						last_pos = end_pos
						end_line = self.view.full_line(end_pos)
						end_line_contents = self.view.substr(end_line)
						if self.view.indentation_level(end_pos) == 0 \
						and end_line_contents.strip() != '' \
						and not end_line_contents.startswith("--"):
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
			
			# print("------")
			# print("Sending: ", file_name)
			# print("Sending contents:")
			# print(line_contents)
			# print("------")
			return line_contents


# Starts the project or runs the current file if rapid project file does not exist.
class RapidRunProjectOrFile(sublime_plugin.WindowCommand):
	def run(self):
		self.view = self.window.active_view()
		self.view.run_command('rapid_output_view_clear')

		#RapidOutputView.printMessage("Loading project settings...")
		startup_path = RapidSettings().getStartupFilePath()
		#RapidOutputView.printMessage("Startup path: " + startup_path)

		RapidStartExecutable()

		if startup_path:
			# Run project
			RapidOutputView.printMessage("Run project: " + startup_path)
			line = "\nsys.loadProject([[" + startup_path + "]])"
			RapidConnectionThread.sendString(line)
		else:
			# Run file
			file = self.view.file_name()
			ext = os.path.splitext(file)[1]
			if self.view.is_dirty():
				RapidOutputView.printMessage("Cannot run current file because the file has changes.")
			elif ext != ".lua":
				RapidOutputView.printMessage("Cannot run current file because the file does not have .lua extension.")
			else:
				RapidOutputView.printMessage("Run file: " + file)
				RapidConnectionThread.sendString("\nsys.loadProject([[" + file + "]])")


# Starts the rapid executable if it's not already running.
class RapidStartExecutable():
	def __init__(self):
		rapid_path = None # Location of the rapid executable
		rapid_name = None # Executable name without extension (e.g. "rapid")

		# Find rapid executable from project file
		settings = RapidSettings().getSettings()
		if "RapidExe" in settings:
			rapid_name = settings["RapidExe"]
		if os.name == "nt":
			if "RapidPathWin" in settings:
				os.chdir(RapidSettings().getStartupProjectPath()) 
				rapid_path = os.path.realpath(settings["RapidPathWin"])
		elif os.name == "posix":
			if "RapidPathOSX" in settings:
				os.chdir(RapidSettings().getStartupProjectPath()) 
				rapid_path = os.path.realpath(settings["RapidPathOSX"])

		# Fall back to plugin settings if not found
		if not rapid_path or not rapid_name:
			plugin_settings = sublime.load_settings("Rapid.sublime-settings")
			rapid_executable_path = plugin_settings.get("rapid_executable")
			if rapid_executable_path:
				rapid_path = os.path.dirname(rapid_executable_path)
				rapid_name = os.path.splitext(os.path.basename(rapid_executable_path))[0]

		if not rapid_path or not rapid_name:
			RapidOutputView.printMessage("Could not find rapid executable in plugin settings or project file!")
			return

		#RapidOutputView.printMessage("rapid_path:" + str(rapid_path))
		#RapidOutputView.printMessage("rapid_name:" + str(rapid_name))

		# Check if the executable is already running and exit if so
		if os.name == "nt":
			if self.isProcessRunning(rapid_name + ".exe") or self.isProcessRunning(rapid_name + "_d.exe"):
				#RapidOutputView.printMessage("Rapid executable is running")
				return
		elif os.name == "posix":
			data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
			for line in data:
				lineStr = line.decode("utf-8")
				if lineStr.find(rapid_name) > -1 and lineStr.find(os.getlogin()) > -1:
					#RapidOutputView.printMessage("Rapid executable is running")
					return

		# Do not attempt to run the executable if the server is not running on the host PC
		if "Host" in settings and settings["Host"] != "localhost" and settings["Host"] != "127.0.0.1":
			return

		# Start the executable
		#RapidOutputView.printMessage("Starting " + rapid_name)
		full_path = os.path.abspath(os.path.join(rapid_path, rapid_name))
		subprocess.Popen(full_path, cwd = rapid_path)
		if os.name == "posix":
			time.sleep(0.5) # Small delay to get server running on OSX

	def isProcessRunning(self, process_name):
		proc = subprocess.Popen(
				'tasklist /FI "IMAGENAME eq ' + process_name + '" /FO CSV /NH',
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
				shell = True
			)
		result, _ = proc.communicate()
		return process_name.encode() in result


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