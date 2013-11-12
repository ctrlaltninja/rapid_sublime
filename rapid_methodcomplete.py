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

from os.path import basename
from .rapid_output import RapidOutputView

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

class CollectorThread(threading.Thread):
	instance = None
	MAX_WORD_SIZE = 100
	MAX_FUNC_SIZE = 50

	def __init__(self, folders, timeout):
		self.folders = folders
		self.timeout = timeout
		threading.Thread.__init__(self)
		CollectorThread.instance = self

	def save_method_signature(self, file_name):
		file_lines = open(file_name, 'rU')
		for line in file_lines:
			if "function" in line:
				matches = re.search('function\s\w+[:\.](\w+)\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				if matches != None and (len(matches.group(1)) < self.MAX_FUNC_SIZE and len(matches.group(2)) < self.MAX_FUNC_SIZE):
					FunctionStorage.addFunction(matches.group(1), matches.group(2), basename(file_name))
				elif matches2 != None and (len(matches2.group(1)) < self.MAX_FUNC_SIZE and len(matches2.group(2)) < self.MAX_FUNC_SIZE):
					FunctionStorage.addFunction(matches2.group(1), matches2.group(2), basename(file_name))

	def get_lua_files(self, dir_name, *args):
		fileList = []
		for file in os.listdir(dir_name):
			dirfile = os.path.join(dir_name, file)
			if os.path.isfile(dirfile):
				fileName, fileExtension = os.path.splitext(dirfile)
				if fileExtension == ".lua":
					fileList.append(dirfile)
				elif os.path.isdir(dirfile):
					fileList += self.get_javascript_files(dirfile, *args)     
		return fileList

	def run(self):
		#RapidOutputView.printMessage("Collectorthread run")
		for folder in self.folders:
			luafiles = self.get_lua_files(folder)
			for file_name in luafiles:
				self.save_method_signature(file_name)

	def stop(self):
		if self.isAlive():
			self._Thread__stop()

class FunctionStorage():
	functions = []

	@staticmethod
	def clear():
		FunctionStorage.functions = []

	@staticmethod
	def addFunction(name, signature, filename):
		FunctionStorage.functions.append(Method(name, signature, filename))
	
	@staticmethod
	def getAutoCompleteList(word):
		autocomplete_list = []
		for method_obj in FunctionStorage.functions:
			if word in method_obj.name():
				#	{ "trigger": "crossfade", "contents": "crossfade(${1:name}, ${2:length}, ${3:loop})"},
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

class Collector(sublime_plugin.EventListener):
	
	def on_post_save(self, view):
		#RapidOutputView.printMessage("on_post_save")
		FunctionStorage.clear()
		folders = view.window().folders()
		if CollectorThread.instance != None:
			CollectorThread.instance.stop()
		CollectorThread.instance = CollectorThread(folders, 30)
		CollectorThread.instance.start()
	
	def on_query_completions(self, view, prefix, locations):
		#RapidOutputView.printMessage("on_query_completions")
		completions = []
		if view.file_name() != None and '.lua' in view.file_name():
			return FunctionStorage.getAutoCompleteList(prefix)
		completions.sort()
		return (completions, sublime.INHIBIT_EXPLICIT_COMPLETIONS)


class StartCollectorCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#RapidOutputView.printMessage("start_collector_command")
		FunctionStorage.clear()
		folders = self.view.window().folders()
		if CollectorThread.instance != None:
			CollectorThread.instance.stop()
		CollectorThread.instance = CollectorThread(folders, 30)
		CollectorThread.instance.start()