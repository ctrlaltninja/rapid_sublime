# This file is based on the MySignature Sublime Text Plugin
# Modified to work with Lua files and automatically load function signatures at startup  

#Original header comments:

#-----------------------------------------------------------------------------------
# MySignature Sublime Text Plugin
# Author: Elad Yarkoni
# Version: 1.0
# Description: Sublime text autocomplete improvements: 
#       - showing javascript methods with parameters
#-----------------------------------------------------------------------------------

import sublime, sublime_plugin
import os, re, threading
import time

from os.path import basename
from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings

from .rapid_functionstorage import RapidFunctionStorage
from .rapid_functionstorage import Method
from .rapid_functionstorage import FunctionDefinition

class RapidCollector():
	def __init__(self, folders, excluded_folders):
		self.folders = folders
	
		self.luaFuncPattern = re.compile('\s*function\s*')
		self.cppFuncPattern = re.compile("///\s")

		self.excluded_folders = excluded_folders

	#Save all method signatures from all project folders
	def save_method_signatures(self):
		for folder in self.folders:
			luafiles = []
			cppfiles = []
			self.get_files_in_project(folder, luafiles, cppfiles)

			methodPattern = re.compile('function\s\w+[:\.](\w+)\((.*)\)')
			funcPattern = re.compile('function\s*(\w+)\s*\((.*)\)')

			for file_name in luafiles:
				functions = []
				findFunctions = []
				function_lines = self.findLua(file_name)
				for line in function_lines:
					matches = methodPattern.match(line)
					if matches:
						functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
						findFunctions.append(FunctionDefinition(matches.group(0)))
					else:
						matches = funcPattern.match(line)
						if matches:
							functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
							findFunctions.append(FunctionDefinition(matches.group(0)))
				RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
				RapidFunctionStorage.addFindFunctions(findFunctions, file_name)
		
			for file_name in cppfiles:
				functions = []
				findFunctions = []

				with open(file_name, 'r', encoding="ascii", errors="surrogateescape") as f:
					#print(file_name)
					for line in f:
						matches = self.cppFuncPattern.match(line)
						if matches != None:
							line = line.strip()
							name = None
							signature = None

							# match global functions without return values, e.g. "/// foobar(x, y)"
							matches = re.match('///\s*(\w+)[\({](.*)[\)}]', line)
							if matches != None:
								name = matches.group(1)
								signature = matches.group(2)
							else:
								# match global functions with return values, e.g. "/// baz,boz = foobar(x, y)"
								matches = re.match('///\s*[,\w]+\s*=\s*(\w+)[\({](.*)[\)}]', line)
								if matches != None:
									name = matches.group(1)
									signature = matches.group(2)
								else:
									# match functions without return values, e.g. "/// Foo.bar(x, y)"
									matches = re.match('///\s*\w+[:\.](\w+)[\({](.*)[\)}]', line)
									if matches != None:
										name = matches.group(1)
										signature = matches.group(2)
									else:
										# match functions with return values, e.g. "/// baz,boz = Foo.bar(x, y)"
										matches = re.match('///\s*[,\w]+\s*=\s*\w+[:\.](\w+)[\({](.*)[\)}]', line)
										if matches != None:
											name = matches.group(1)
											signature = matches.group(2)
										elif len(findFunctions) > 0:
											# match description, e.g. "/// blabla"
											matches = re.match('///\s*(.*)', line)
											if matches:
												description = matches.group(1)
												#print("DESC: " + description)
												findFunctions[-1].addDescription(description)

							if name:
								if signature == None:
									signature = ""
								functions.append(Method(name, signature, ""))
								findFunctions.append(FunctionDefinition(line))

						RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
						RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

	def findLua(self, filepath):
		function_list = []
		#print(filepath)
		with open(filepath, 'r', encoding="ascii", errors="surrogateescape") as f:
			for line in f:
				matches = self.luaFuncPattern.match(line)
				if matches != None:
					function_list.append(line.strip())
		return function_list

	#Save method signatures from the given file
	def save_method_signature(self, file_name):
		functions = []
		findFunctions = []
		function_lines = self.findLua(file_name)
		methodPattern = re.compile('function\s\w+[:\.](\w+)\((.*)\)')
		funcPattern = re.compile('function\s*(\w+)\s*\((.*)\)')
		RapidFunctionStorage.removeAutoCompleteFunctions(file_name)
		RapidFunctionStorage.removeFindFunctions(file_name) 
		for line in function_lines:
			matches = methodPattern.match(line)
			if matches:
				functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
				findFunctions.append(FunctionDefinition(matches.group(0)))
			else:
				matches = funcPattern.match(line)
				if matches:
					functions.append(Method(matches.group(1), matches.group(2), basename(file_name)))
					findFunctions.append(FunctionDefinition(matches.group(0)))
		RapidFunctionStorage.addAutoCompleteFunctions(functions, file_name)
		RapidFunctionStorage.addFindFunctions(findFunctions, file_name)

	def get_files_in_project(self, folder, luaFileList, cppFileList):
		for root, dirs, files in os.walk(folder, True):

			# prune excluded folders from search
			for excluded_folder in self.excluded_folders:
				if excluded_folder in dirs:
					#print("Pruning excluded folder " + excluded_folder)
					dirs.remove(excluded_folder)

			for name in files:
				if name.endswith(".lua"):
					full_path = os.path.abspath(os.path.join(root, name))
					luaFileList.append(full_path)
					#add lua file path for static analyzer
					RapidFunctionStorage.addLuaFile(full_path) 
				if name.endswith(".cpp"):
					full_path = os.path.abspath(os.path.join(root, name))
					cppFileList.append(full_path)

class RapidCollectorThread(threading.Thread):
	instance = None
		
	def __init__(self, folders, timeout):
		threading.Thread.__init__(self)
		self.timeout = timeout

		excluded_folders = []
		settings = RapidSettings().getSettings()
		if "ExcludedFolders" in settings:
			excluded_folders = settings["ExcludedFolders"]

		self.collector = RapidCollector(folders, excluded_folders)
		self.collector.save_method_signatures()

		#self.parse_now = False
		self.file_for_parsing = ""
		self.is_running = True

		RapidCollectorThread.instance = self

	#def run(self):
		# #TODO: change this to use callback instead of polling
		# while self.is_running:
		# 	if self.parse_now and self.file_for_parsing:
		# 		self.save_method_signature(self.file_for_parsing)
		# 		self.parse_now = False
		# 	time.sleep(0.1)

	def callback(self):
		#print("Rapid MethodComplete: saving method signature")
		self.collector.save_method_signature(self.file_for_parsing)

	def parseAutoCompleteData(self, view):
		self.file_for_parsing = view.file_name()
		#parse only *.lua files at runtime
		if self.file_for_parsing.endswith(".lua"):
			#print("calling methodcomplete callback")
			sublime.set_timeout(self.callback, 100)
			#self.parse_now = True

	def stop(self):
		self.is_running = False

class RapidCollectorListener(sublime_plugin.EventListener):
	applyAutoComplete = False
	parseAutoComplete = False

	def on_post_save(self, view):
		if RapidCollectorListener.parseAutoComplete:
			RapidCollectorThread.instance.parseAutoCompleteData(view)

	def on_query_completions(self, view, prefix, locations):
		if RapidCollectorListener.applyAutoComplete:
			RapidCollectorListener.applyAutoComplete = False
			syntax = view.settings().get('syntax')
			if syntax != None and 'Lua' in syntax:
				return RapidFunctionStorage.getAutoCompleteList(prefix)
		return None
	
class RapidAutoCompleteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidCollectorListener.applyAutoComplete = True
		self.view.run_command('auto_complete')

class RapidStartCollectorCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("Collecting function definitions for autocomplete...")
		startTime = time.time()

		settings = RapidSettings().getSettings()		
		if "ParseAutoCompleteOnSave" in settings:
			RapidCollectorListener.parseAutoComplete = settings["ParseAutoCompleteOnSave"]
		
		folders = sublime.active_window().folders()
		if RapidCollectorThread.instance != None:
			RapidCollectorThread.instance.stop()
			RapidCollectorThread.instance.join()
		RapidCollectorThread.instance = RapidCollectorThread(folders, 30)

		RapidCollectorThread.instance.start()
		RapidOutputView.printMessage("Collected function signatures in %.2f seconds." % (time.time() - startTime))