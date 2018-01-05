import os
import sublime, sublime_plugin
from .rapid import RapidConnectionThread
from .rapid_output import RapidOutputView
from .rapid_utils import escape_filename
from .rapid_utils import clear_current_row_icons
from .rapid_utils import clear_region_from_all_views

REGION_KEY = "breakpoint"

def send_cmd(cmd):
	RapidConnectionThread.sendString("\n" + cmd)

def out(msg):
	RapidOutputView.printMessage("Debug: " + msg)

class RapidDebugRunCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.run()")
		out("Running...")
		clear_current_row_icons()

class RapidDebugStepCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.step()")

class RapidDebugToggleBreakpoint(sublime_plugin.TextCommand):
	def run(self, edit):
		# fudge selections to contain full lines so that column location does not matter
		toggled_points = [self.view.line(r.begin()).begin() for r in self.view.sel()]

		previous_points = [r.begin() for r in self.view.get_regions(REGION_KEY)]

		new_points = [p for p in toggled_points if not p in previous_points]
		removed_points = [p for p in toggled_points if p in previous_points]
		current_points = list(set().union(previous_points, new_points).difference(removed_points))

		regions = [sublime.Region(point, point) for point in current_points]

		self.view.add_regions(REGION_KEY, regions, "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

		filename = os.path.basename(self.view.file_name())

		# call add breakpoint for all valid breakpoints
		for point in new_points:
			row,_ = self.view.rowcol(point)
			self.setBreakpoint(filename, row + 1)

		# call remove breakpoint for all old breakpoints
		for point in removed_points:
			row,_ = self.view.rowcol(point)
			self.removeBreakpoint(filename, row + 1)

	def setBreakpoint(self, filename, row):
		filename = escape_filename(filename)
		message = "Debug.addBreakpoint(\"%(file)s\", %(row)d)" % { 'file': filename, 'row': row }
		send_cmd(message)

	def removeBreakpoint(self, filename, row):
		filename = escape_filename(filename)
		message = "Debug.removeBreakpoint(\"%(file)s\", %(row)d)" % { 'file': filename, 'row': row }
		send_cmd(message)

class RapidDebugRemoveAllBreakpoints(sublime_plugin.TextCommand):
	def run(self, edit):
		send_cmd("Debug.removeAllBreakpoints()")

		clear_region_from_all_views(REGION_KEY)

class RapidDebugStartSessionCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		super().__init__(window)
		self.active = False
		self.cmds = {
			'cb': self.remove_all_breakpoints,
			'g': self.go,
			'p': self.ping,
			'idle': self.idle,
			'q': self.stop,
		}

	def run(self):
		# Signal the server side that we want to start debugging
		send_cmd("Debug.start()")
		self.show_panel()
		self.active = True
		out("Started.")

	def show_panel(self):
		self.view = self.window.show_input_panel(
			"Debug", "",
			lambda t: self.committed(t),
			None, #lambda t: self.changed(t),
			self.canceled)

	def committed(self, text):
		# Parse the command
		text = text.strip() or "idle"
		cmd = self.cmds[text]

		if cmd:
			cmd()
		else:
			# TODO
			pass

		# reshow the input panel unless explicitly closed
		if self.active:
			self.show_panel()

	def canceled(self):
		self.active = False

	def go(self):
		self.window.run_command("rapid_debug_run")

	def idle(self):
		out("---")

	def ping(self):
		out("Ping!")
		send_cmd("print('Pong!')")

	def remove_all_breakpoints(self):
		self.window.run_command("rapid_debug_remove_all_breakpoints")

	def stop(self):
		self.window.run_command("rapid_debug_stop_session")
		self.active = False
		out("Stopped.")


class RapidDebugStopSessionCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.stop()")