import sublime, sublime_plugin
from .rapid_utils import open_file_location
from .rapid_utils import escape_filename
from .rapid import RapidConnectionThread

REGION_KEY = "breakpoint"

class RapidDebugStepCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.sendString("\nDebug.step()")

class RapidDebugToggleBreakpoint(sublime_plugin.TextCommand):
	def run(self, edit):
		# BUG the breakpoint location is dependent on the column -> fudge selections to start from the
		# beginning of the line for toggled points
		previous_points = [r.begin() for r in self.view.get_regions(REGION_KEY)]
		toggled_points = [r.begin() for r in self.view.sel()]

		new_points = [p for p in toggled_points if not p in previous_points]
		removed_points = [p for p in toggled_points if p in previous_points]
		current_points = list(set().union(previous_points, new_points).difference(removed_points))

		regions = [sublime.Region(point, point) for point in current_points]

		self.view.add_regions(REGION_KEY, regions, "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

		filename = self.view.file_name()

		# call add breakpoint for all valid breakpoints
		for point in new_points:
			row,_ = self.view.rowcol(point)
			self.setBreakpoint(filename, row)

		# call remove breakpoint for all old breakpoints
		for point in removed_points:
			row,_ = self.view.rowcol(point)
			self.removeBreakpoint(filename, row)

	def setBreakpoint(self, filename, row):
		filename = escape_filename(filename)
		message = "\nDebug.addBreakpoint(\"%(file)s\", %(row)d)" % { 'file': filename, 'row': row }
		RapidConnectionThread.sendString(message)

	def removeBreakpoint(self, filename, row):
		filename = escape_filename(filename)
		message = "\nDebug.removeBreakpoint(\"%(file)s\", %(row)d)" % { 'file': filename, 'row': row }
		RapidConnectionThread.sendString(message)

class RapidDebugRemoveAllBreakpoints(sublime_plugin.TextCommand):
	def run(self, edit):
		RapidConnectionThread.sendString("\nDebug.removeAllBreakpoints()")
		self.view.erase_regions(REGION_KEY)

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