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

def _find_impl(command, edit, full):
	cursor_pos = command.view.sel()[0].begin()

	region = command.view.word(cursor_pos)
	pattern = command.view.substr(region)
	#print("Pattern is: " + pattern)
	#RapidOutputView.printMessage("Pattern is: " + pattern)

	if len(pattern) == 0:
		RapidOutputView.printMessage("Find: empty search patterns are no good.")
		return

	# Figure out if this a call site or not
	word_end_pos = max(region.a, region.b)
	callsite = "(" == command.view.substr(sublime.Region(word_end_pos, word_end_pos + 1))

	# Check left and right from the pattern word: if there is a dot or
	# a wildcard, we are checking for classes and the selection should be expanded
	find_class_methods = False
	left = command.view.substr(sublime.Region(region.begin()-1, region.begin()))
	right = command.view.substr(sublime.Region(region.end(), region.end()+1))

	if left == '.' or left == '*' or right == '.' or right == '*':
		find_class_methods = True
		region = command.view.expand_by_class(region, sublime.CLASS_LINE_START | sublime.CLASS_LINE_END, ".* \t")
		pattern = command.view.substr(region)

	pattern2 = pattern.lower().strip()

	found = False
	find_fun = findClass if find_class_methods else find

	for match in find_fun(pattern2, callsite):
		found = True

		# signature
		RapidOutputView.printMessage(match[0] + "\n") 

		 # description
		if full and match[1]:
			# TODO go through /// and remove extra line breaks -> this works nicer
			RapidOutputView.printMessage("\t" + match[1] + "\n")

	if found:
		RapidOutputView.printMessage("\n")
	else:
		RapidOutputView.printMessage("Find: no match for \"" + pattern +"\"")

class RapidFindShortCommand(sublime_plugin.TextCommand):
	def run(self, edit): _find_impl(self, edit, False)

class RapidFindFullCommand(sublime_plugin.TextCommand):
	def run(self, edit): _find_impl(self, edit, True)