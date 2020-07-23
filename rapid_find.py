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

	pattern = pattern.replace('.', r'\.')
	final_pattern = None

	if callsite:
		final_pattern = '[\s\.]%s[\({].*[\)}]' % pattern
	else:
		final_pattern = '.*%s.*[\({].*[\)}]' % pattern
	# print(final_pattern)

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

def is_symbol_char(char):
	return char.isalpha() or char in ['.','_','*']

def expand_region(view, region):
	# expand left
	while True:
		left = view.substr(sublime.Region(region.begin()-1, region.begin()))
		if left and is_symbol_char(left):
			region = sublime.Region(region.begin()-1, region.end())
		else:
			break

	# expand right
	while True:
		right = view.substr(sublime.Region(region.end(), region.end()+1))
		if right and is_symbol_char(right):
			region = sublime.Region(region.end(), region.end()+1)
		else:
			break

	return region

def _find_impl(command, edit, full):
	cursor_pos = command.view.sel()[0].begin()

	region = command.view.word(cursor_pos)
	pattern = command.view.substr(region)
	#print("Pattern is: " + pattern)
	#RapidOutputView.printMessage("Pattern is: " + pattern)

	if len(pattern) == 0:
		RapidOutputView.printMessage("Find: empty search patterns are no good.")
		return

	# Check left and right from the pattern word: if there is a dot or
	# a wildcard, we are checking for classes and the selection should be expanded
	left = command.view.substr(sublime.Region(region.begin()-1, region.begin()))
	right = command.view.substr(sublime.Region(region.end(), region.end()+1))

	if left == '.' or left == '*' or right == '.' or right == '*':
		region = expand_region(command.view, region)
		pattern = command.view.substr(region)

	# Figure out if this a call site or not
	word_end_pos = max(region.a, region.b)
	callsite = "(" == command.view.substr(sublime.Region(word_end_pos, word_end_pos + 1))

	pattern = pattern.lower().strip()

	found = False

	for match in find(pattern, callsite):
		found = True

		# signature
		RapidOutputView.printMessage(match[0] + "\n") 

		 # description
		if full and match[1]:
			# replace line breaks with line break + tab to add simple indentation
			RapidOutputView.printMessage("\t" + match[1].replace("\n", "\n\t") + "\n\n")

	if found:
		RapidOutputView.printMessage("\n")
	else:
		RapidOutputView.printMessage("Find: no match for \"" + pattern +"\"")

class RapidFindShortCommand(sublime_plugin.TextCommand):
	def run(self, edit): _find_impl(self, edit, False)

class RapidFindFullCommand(sublime_plugin.TextCommand):
	def run(self, edit): _find_impl(self, edit, True)