import sublime, sublime_plugin
import time
import re

from .rapid_output import RapidOutputView
from .rapid import open_file_location

# to run execute from the console:
# view.run_command('rapid_eval')

class RapidDebugStepCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.sendString("\nDebug.step()")

class RapidDebugToggleBreakpoint(sublime_plugin.TextCommand):
	def run(self, edit):
		region = [s for s in self.view.sel()]
		# TODO: remove breakpoint
		self.view.add_regions("breakpoint", region, "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

class RapidDebugRemoveAllBreakpoints(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.erase_regions("breakpoint")

def parseDebugMessage(cmd):
	matches = re.match('#ATLINE (.*):(.*)', cmd)
	if matches:
		filename = matches.group(1)
		line = matches.group(2)

		open_file_location(filename, line)

		# show current line in gutter
		view = sublime.active_window().active_view()
		region = [s for s in view.sel()]
		icon = "Packages/rapid_sublime/icons/current_line.png"
		view.add_regions("current", region, "mark", icon, sublime.HIDDEN)
	return

class RapidJumpTo(sublime_plugin.WindowCommand):
	def run(self):
		RapidOutputView.printMessage("RapidJumpTo called!")
		print("RapidJumpTo called!")
		path = "c:\\work\\projects\\grimrock2\\Grimrock.lua"
		line = 3
		view = self.window.find_open_file(path)
		if view:
			self.window.open_file(path + ":" + str(line), sublime.ENCODED_POSITION)
			#self.window.focus_view(view)
		else:
			print("file not open -> opening")
			view = self.window.open_file(path + ":" + str(line), sublime.ENCODED_POSITION)
			#if view:
		 	#	self.window.focus_view(view)
