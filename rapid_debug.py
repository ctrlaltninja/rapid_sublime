import sublime, sublime_plugin
import time
import re

from .rapid_output import RapidOutputView
from .rapid_utils import open_file_location
from .rapid_utils import escape_filename
from .rapid import RapidConnectionThread

# to run execute from the console:
# view.run_command('rapid_eval')

class RapidDebugStepCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.sendString("\nDebug.step()")

class RapidDebugToggleBreakpoint(sublime_plugin.TextCommand):
	def run(self, edit):
		# TODO: remove breakpoints
		regions = [s for s in self.view.sel()]
		filename = self.view.file_name()

		for region in regions:
			row,_ = self.view.rowcol(region.begin())
			self.setBreakpoint(filename, row)

		self.view.add_regions("breakpoint", regions, "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

	def setBreakpoint(self, filename, row):
		filename = escape_filename(filename)
		message = "\nDebug.addBreakpoint(\"%(file)s\", %(row)d)" % { 'file': filename, 'row': row }
		RapidConnectionThread.sendString(message)

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