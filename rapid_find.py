import sublime, sublime_plugin
import os
import re
import io

import time

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings
from .rapid_functionstorage import RapidFunctionStorage

class RapidFindCommand(sublime_plugin.TextCommand):
	functionFound = False

	def run(self, edit):
		self.functionFound = False
		cursor_pos = self.view.sel()[0].begin()
		
		region = self.view.word(cursor_pos)
		pattern = self.view.substr(region)
		print("Pattern is: " + pattern)
		#RapidOutputView.printMessage("Pattern is: " + pattern)

		region2 = self.view.line(cursor_pos)
		line = self.view.substr(region2)
		words = line.split()
		
		#RapidOutputView.printMessage("Words are: " + str(words))

		for word in words:
			if "*" in word:
				#Handle edge cases for class find
				if (pattern in word or 
					"*\n" in pattern or "* " in pattern or 
					"\n*" in pattern or " *" in pattern):
					pattern = word
					break

		find_class_methods = False
		if "*" in pattern and "." in pattern:
			find_class_methods = True
		
		pattern2 = pattern.lower().strip()

		if find_class_methods:
			self.findClass(pattern2)
		elif len(pattern) > 0:
			self.find(pattern2)

		if not self.functionFound:
			RapidOutputView.printMessage("Find: no match for \"" + pattern +"\"")

	##########################################
	# Find word(s) from function definitions #
	##########################################

	def find(self, pattern):	
		if pattern.startswith("*"):
			pattern = pattern[1:]

		pattern = '.*'+pattern+'.*[\({].*[\)}]'
		#print("find word(s), pattern: " + pattern)

		functions = RapidFunctionStorage.getFindFunctions()
		if len(functions) == 0:
			# TODO just trigger the recollection from here...
			print("Error: Function definitions have been lost, alt+l collects them again")
		else:
			for func in functions:
				funcName = func.getFunction()
				match = re.search(pattern, funcName.lower())
				if match != None:
					funcName = funcName.replace("///", "").strip()
					RapidOutputView.printMessage(funcName)
					if func.getDescription() != None:
						RapidOutputView.printMessage(func.getDescription())
					self.functionFound = True

	############################################
	# Find class(es) from function definitions #
	############################################

	def findClass(self, pattern):
		if pattern.startswith("*"):
			pattern = pattern[1:]

		#convert wildcards to regular expression
		pattern = pattern.replace('.', '[\.:]').replace('*', '.*')
		search_pattern = pattern + '[\({].*[\)}]'		
		#print("find class, pattern: " + pattern)
		#print("find class, search pattern: " + search_pattern)

		functions = RapidFunctionStorage.getFindFunctions()
		if len(functions) == 0:
			# TODO just trigger the recollection from here...
			print("Error: Function definitions have been lost, alt+l collects them again")
		else:
			for func in functions:
				funcName = func.getFunction()
				match = re.search(search_pattern, funcName.lower())
				if match != None:
					funcName = funcName.strip()
					RapidOutputView.printMessage(funcName)
					if func.getDescription() != None:
						RapidOutputView.printMessage(func.getDescription())
					self.functionFound = True