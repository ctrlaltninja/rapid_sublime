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

class Method:
	_name = ""
	_signature = ""
	_filename = ""
	
	def __init__(self, name, signature, filename):
		self._name = name
		self._filename = filename;
		self._signature = signature

	def name(self):
		return self._name

	def signature(self):
		return self._signature
  
	def filename(self):
		return self._filename

class RapidCollectorThread(threading.Thread):
	instance = None
	MAX_WORD_SIZE = 100
	MAX_FUNC_SIZE = 50

	def getExcludedFolders(self):
		settings = RapidSettings().getSettings()		
		if "ExcludeFoldersInFind" in settings:
			self.exclude_folders = settings["ExcludeFoldersInFind"]
		if "ExcludedFolders" in settings:
			self.excluded_folders = settings["ExcludedFolders"]

		#print("Exclude folders: " + str(self.exclude_folders))
		#print("Excluded folders: " + str(self.excluded_folders))
			
	def __init__(self, folders, timeout):
		self.folders = folders
		self.timeout = timeout
		self.exclude_folders = False
		self.excluded_folders = []
		self.getExcludedFolders()
		threading.Thread.__init__(self)
		RapidCollectorThread.instance = self

	def save_method_signature(self, file_name):
		file_lines = open(file_name, 'r')
		for line in file_lines:
			if "function" in line:
				matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				if matches != None and (len(matches.group(1)) < self.MAX_FUNC_SIZE and len(matches.group(2)) < self.MAX_FUNC_SIZE):
					RapidFunctionStorage.addFunction(matches.group(1), matches.group(2), basename(file_name))
				elif matches2 != None and (len(matches2.group(1)) < self.MAX_FUNC_SIZE and len(matches2.group(2)) < self.MAX_FUNC_SIZE):
					RapidFunctionStorage.addFunction(matches2.group(1), matches2.group(2), basename(file_name))

	# def get_lua_files(self, dir_name, *args):
	# 	fileList = []
	# 	for file in os.listdir(dir_name):
	# 		dirfile = os.path.join(dir_name, file)
	# 		if os.path.isfile(dirfile):
	# 			fileName, fileExtension = os.path.splitext(dirfile)
	# 			if fileExtension == ".lua":
	# 				fileList.append(dirfile)
	# 			elif os.path.isdir(dirfile):
	# 				fileList += self.get_javascript_files(dirfile, *args) 

	# 	print("File list size: " + str(len(fileList)))    
	# 	return fileList

	def get_lua_files2(self, folder, *args):
		fileList = []
		for root, dirs, files in os.walk(folder):
			
			checkFolder = True
			if self.exclude_folders:
				for excluded_folder in self.excluded_folders:
					if root.lower().startswith(excluded_folder.lower()):			
						checkFolder = False 
						break
				if not checkFolder:
				 	continue
						
			for name in files:
				if name.endswith("lua"):
					full_path = os.path.abspath(os.path.join(root, name))
					fileList.append(full_path)

		#print("File list size: " + str(len(fileList)))    
		return fileList

	def run(self):
		for folder in self.folders:
			luafiles = self.get_lua_files2(folder)
			for file_name in luafiles:
				self.save_method_signature(file_name)

	def stop(self):
		if self.isAlive():
			self._Thread__stop()

class RapidFunctionStorage():
	functions = []

	@staticmethod
	def clear():
		RapidFunctionStorage.functions = []

	@staticmethod
	def addFunction(name, signature, filename):
		#print("adding function " + name + ", " + signature + ", " + filename)
		RapidFunctionStorage.functions.append(Method(name, signature, filename))
	
	@staticmethod
	def getAutoCompleteList(word):
		autocomplete_list = []
		for method_obj in RapidFunctionStorage.functions:
			if word.lower() in method_obj.name().lower():
				
				#parse method variables
				variables = method_obj.signature().split(",")
				signature = ""
				index = 1
				for variable in variables:
					signature = signature + "${"+str(index)+":"+variable+"}"
					if index < len(variables):
						signature = signature + ", "
					index = index+1

				method_str_to_show = method_obj.name() + '(' + method_obj.signature() +')'
				method_str_to_append = method_obj.name() + '(' + signature + ')'
				method_file_location = method_obj.filename();
				autocomplete_list.append((method_str_to_show + '\t' + method_file_location, method_str_to_append)) 
		return autocomplete_list	

class RapidCollector(sublime_plugin.EventListener):
	applyAutoComplete = False

	def on_post_save(self, view):
		RapidFunctionStorage.clear()
		folders = view.window().folders()
		if RapidCollectorThread.instance != None:
			RapidCollectorThread.instance.stop()
		RapidCollectorThread.instance = RapidCollectorThread(folders, 30)
		RapidCollectorThread.instance.start()

	def on_query_completions(self, view, prefix, locations):
		#print("on_query_completions: " + str(RapidCollector.applyAutoComplete))
		if RapidCollector.applyAutoComplete:
			RapidCollector.applyAutoComplete = False
			if view.file_name() != None and '.lua' in view.file_name():
				return RapidFunctionStorage.getAutoCompleteList(prefix)
		completions = []
		#print("Returning standard stuff")
		return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)
	
	# def on_query_completions(self, view, prefix, locations):
	# 	completions = []
	# 	if view.file_name() != None and '.lua' in view.file_name():
	# 		return RapidFunctionStorage.getAutoCompleteList(prefix)
	# 	completions.sort()
	# 	return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)

class RapidAutoCompleteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#print("AutoCompleteCommand start")
		RapidCollector.applyAutoComplete = True
		self.view.run_command('auto_complete')

class RapidStartCollectorCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		print("Collecting function definitions for autocomplete...")
		RapidFunctionStorage.clear()
		folders = self.view.window().folders()
		if RapidCollectorThread.instance != None:
			RapidCollectorThread.instance.stop()
		RapidCollectorThread.instance = RapidCollectorThread(folders, 30)
		RapidCollectorThread.instance.start()