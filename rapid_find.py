import sublime, sublime_plugin
import os
import re
import io

import time

from .rapid_output import RapidOutputView
from .rapid_parse import RapidSettings
from .rapid_functionstorage import RapidFunctionStorage

# Find word(s) from function definitions
def find(pattern, callsite=False):	
	if pattern.startswith("*"):
		pattern = pattern[1:]

	final_pattern = None

	if callsite:
		final_pattern = '\s%s[\({].*[\)}]' % pattern
	else:
		final_pattern = '.*%s.*[\({].*[\)}]' % pattern

	functions = RapidFunctionStorage.getFindFunctions()
	if len(functions) == 0:
		# TODO just trigger the recollection from here...
		print("Error: Function definitions have been lost, alt+l collects them again")
		return
	else:
		for func in functions:
			funcName = func.getFunction()
			match = re.search(final_pattern, funcName.lower())
			if match != None:
				# TODO strip already when scanning
				funcName = funcName.replace("///", "").strip()
				yield (funcName, func.getDescription())

# Find class(es) from function definitions
def findClass(pattern, callsite=False):
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
		return
	else:
		for func in functions:
			funcName = func.getFunction()
			# TODO strip already when scanning
			funcName = funcName.replace("///", "").strip()
			# TODO is forcing it to lower a bug or not? It does not match e.g. pattern Foo.bar or Foo:bar
			match = re.search(search_pattern, funcName.lower())
			if match != None:
				funcName = funcName.strip()
				yield (funcName, func.getDescription())

def find_impl(command, edit, full):
	cursor_pos = command.view.sel()[0].begin()
	
	region = command.view.word(cursor_pos)
	pattern = command.view.substr(region)
	print("Pattern is: " + pattern)
	#RapidOutputView.printMessage("Pattern is: " + pattern)

	if len(pattern) == 0:
		RapidOutputView.printMessage("Find: empty search patterns are no good.")
		return

	# Figure out if this a call site or not
	word_end_pos = max(region.a, region.b)
	callsite = "(" == command.view.substr(sublime.Region(word_end_pos, word_end_pos + 1))

	words = command.view.substr(command.view.line(cursor_pos)).split()
	
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

	found = False
	find_fun = findClass if find_class_methods else find

	for match in find_fun(pattern2, callsite):
		found = True

		# signature
		RapidOutputView.printMessage(match[0]) 

		 # description
		if full and match[1]:
			RapidOutputView.printMessage(match[1])

	if not found:
		RapidOutputView.printMessage("Find: no match for \"" + pattern +"\"")

class RapidFindShortCommand(sublime_plugin.TextCommand):
	def run(self, edit): find_impl(self, edit, False)

class RapidFindFullCommand(sublime_plugin.TextCommand):
	def run(self, edit): find_impl(self, edit, True)