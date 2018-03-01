import sublime, sublime_plugin
import re
import os
import sublime_api
from .rapid_utils import open_file_location

tailing = True

def parse_file_location(line):
	file_name_and_row = None

	# leave out lambdas: match with and without surrounding <>,
	# but do not capture if surrounded with <>:
	groups = re.findall(r"([-/\w\d:\.]+:\d+)|(?:<.+>)", line)

	# filter out all empty strings the latter match may produce
	groups = [g for g in groups if g != '']

	if len(groups) > 0:
		file_name_and_row = groups[-1]

	if file_name_and_row and file_name_and_row != '':
		#split on the last occurence of ':'
		test = file_name_and_row.rsplit(':', 1)
		file_name = test[0].strip()
		file_row = int(test[1])

		return file_name, file_row
	else:
		return None, None

def scroll_to_tail(view):
	region = view.full_line(view.size())
	view.show(region)

class RapidOutputView():
	name = "Rapid Output"
	analyze_view_name = "Analyze Result"
	analyze_file_name = "analyze_result.lua"

	messageQueue = []

	@classmethod
	def getOutputView(self, create):
		for window in sublime.windows():
			for view in window.views():
				if view.name() == RapidOutputView.name:
					return view

		# create new view
		if create:
			window = sublime.active_window()
			activeView = window.active_view()
			groups = window.num_groups()
			if groups < 2:
				window.set_layout( {"cols": [0.0, 1.0], "rows": [0.0, 0.8, 1.0], "cells": [[0,0,1,1], [0,1,1,2]]} )
			window.focus_group(1)
			outputView = window.new_file()
			outputView.set_read_only(True)
			outputView.set_scratch(True)
			outputView.set_name(RapidOutputView.name)
			window.set_view_index(outputView, 1, 0)
			window.focus_view(activeView)
			#if outputView.settings().get('syntax') != "Packages/Lua/Lua.tmLanguage":
			outputView.set_syntax_file("Packages/Lua/Lua.tmLanguage")		
			return outputView
			
		return None

	@classmethod
	def printMessage(self, msg):
		RapidOutputView.messageQueue.append(msg)
		if len(RapidOutputView.messageQueue) == 1:
			sublime.set_timeout(RapidOutputView.callback, 100)
			
	@classmethod
	def callback(self):
		view = RapidOutputView.getOutputView(True)
		while len(RapidOutputView.messageQueue) > 0:
			msg = RapidOutputView.messageQueue.pop(0)
			view.run_command("rapid_output_view_insert", {"msg": msg } )
			
class RapidOutputViewInsertCommand(sublime_plugin.TextCommand):
	def run(self, edit, msg):
		global tailing
		view = self.view

		if not '\n' in msg:
			msg = msg + '\n'
		
		#if re.search("Static analysis done", msg):
		#	self.view.window().run_command("rapid_luacheck_load_static_analysis")
		#	return

		view.set_read_only(False)
		view.insert(edit, view.size(), msg)
		view.set_read_only(True)

		if tailing:
			scroll_to_tail(view)

class RapidOutputViewClearCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = RapidOutputView.getOutputView(True)
		if view != None:
			view.set_read_only(False)
			view.erase(edit, sublime.Region(0, view.size()))
			view.set_read_only(True)

class RapidDoubleClick(sublime_plugin.WindowCommand):
	def run(self):
		view = sublime.active_window().active_view()
		if view.name() == RapidOutputView.name or view.name() == RapidOutputView.analyze_view_name or \
						  (view.file_name() != None and view.file_name().endswith(RapidOutputView.analyze_file_name)):

			# If there are multiple selected areas, just pick the first:
			line = view.substr(view.line(view.sel()[0]))
			line = line.replace('\\', '/')

			file_name, file_row = parse_file_location(line)
			if file_name:
				success, err = open_file_location(file_name, file_row)
				view.run_command("expand_selection", {"to": "line"})
				if not success:
					RapidOutputView.printMessage(err)
			else:
				print("Rapid: Could not parse file name from selection:", line)

class RapidCloseOutputViewCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		#print("Rapid Close Output View command")
		view = RapidOutputView.getOutputView(False)
		if view != None:
			self.view.window().focus_view(view)
			self.view.window().run_command("close_file")

class RapidToggleTailingCommand(sublime_plugin.WindowCommand):
	def run(self):
		global tailing
		tailing = not tailing
		view = RapidOutputView.getOutputView(False)
		if view and tailing:
			view.erase_status("rapid_tailing")
			scroll_to_tail(view)
		elif view:
			view.set_status("rapid_tailing", "*NO TAILING*")

class RapidOutputEventListener(sublime_plugin.EventListener):
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "close_server_output":
			for window in sublime.windows():
				for view in window.views():
					if view.name() == RapidOutputView.name:
						return True
		return False