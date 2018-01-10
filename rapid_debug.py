import os
import re
import sublime, sublime_plugin
from .rapid import RapidConnectionThread
from .rapid_base import editorState
from .rapid_output import RapidOutputView
from .rapid_utils import escape_filename
from .rapid_utils import clear_current_row_icons
from .rapid_utils import clear_region_from_all_views
from .rapid_utils import escape_lua_string

REGION_KEY = "breakpoint"

def send_cmd(cmd):
	RapidConnectionThread.sendString("\n" + cmd)

def out(msg):
	RapidOutputView.printMessage("Debug: " + msg)

class RapidDebugRunCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.run()")
		editorState.run()
		out("Running...")
		clear_current_row_icons()

class RapidDebugStepCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.step()")
		editorState.run()

class RapidDebugToggleBreakpoint(sublime_plugin.TextCommand):
	def run(self, edit):

		filename = self.view.file_name()

		if not filename:
			out("Please save the file first - a file name is needed for the breakpoint to be effective.")
			return

		# fudge selections to contain full lines so that column location does not matter
		toggled_points = [self.view.line(r.begin()).begin() for r in self.view.sel()]

		previous_points = [r.begin() for r in self.view.get_regions(REGION_KEY)]

		new_points = [p for p in toggled_points if not p in previous_points]
		removed_points = [p for p in toggled_points if p in previous_points]
		current_points = list(set().union(previous_points, new_points).difference(removed_points))

		regions = [sublime.Region(point, point) for point in current_points]

		self.view.add_regions(REGION_KEY, regions, "mark", "dot", sublime.HIDDEN | sublime.PERSISTENT)

		filename = os.path.basename(filename)

		# call add breakpoint for all valid breakpoints
		for point in new_points:
			row,_ = self.view.rowcol(point)
			self.setBreakpoint(filename, row + 1)

		# call remove breakpoint for all old breakpoints
		for point in removed_points:
			row,_ = self.view.rowcol(point)
			self.removeBreakpoint(filename, row + 1)

		if len(new_points) > 0 and not editorState.debugging:
			self.view.window().run_command("rapid_debug_start_session", { 'session': 'start' })

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

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

Command = enum(
	'UNKNOWN',
	'DUMP',
	'HELP',
	'IDLE',
	'PING',
	'REMOVE_ALL_BREAKPOINTS',
	'RUN',
	'STOP'
)

command_map = {
	'cb': Command.REMOVE_ALL_BREAKPOINTS,
	'd': Command.DUMP,
	'g': Command.RUN,
	'h': Command.HELP,
	'help': Command.HELP,
	'idle': Command.IDLE,
	'p': Command.PING,
	'q': Command.STOP,
}

def parse_debug_command(text):
	matches = re.match('^(\w+)\s*(?:\s(\S+)|$)', text)

	if matches:
		result = command_map.get(matches.group(1)) or Command.UNKNOWN
		return (result, [matches.group(2)] if matches.group(2) else None)
	else:
		return (Command.UNKNOWN, None)

class RapidDebugStartSessionCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		super().__init__(window)
		self.active = False
		# TODO use metaprogramming to generate this on the fly
		self.method_map = {
			Command.DUMP					: self.dump,
			Command.HELP					: self.help,
			Command.IDLE					: self.idle,
			Command.PING					: self.ping,
			Command.REMOVE_ALL_BREAKPOINTS	: self.remove_all_breakpoints,
			Command.RUN						: self.go,
			Command.STOP					: self.stop,
			Command.UNKNOWN					: self.unknown,
		}

	def run(self, session = "start"):
		if session == "start":
			# Signal the server side that we want to start debugging
			send_cmd("Debug.start()")
			out("Started.")
			editorState.startDebugging()

		self.active = True
		self.show_panel()

	def show_panel(self):
		self.view = self.window.show_input_panel(
			"Debug", "",
			lambda t: self.committed(t),
			None, #lambda t: self.changed(t),
			self.canceled)

	def committed(self, text):
		# Parse the command
		text = text.strip() or "idle"
		command, params = parse_debug_command(text)

		if params:
			method = self.method_map[command](params)
		else:
			method = self.method_map[command]()

		# reshow the input panel unless explicitly closed
		if self.active:
			self.show_panel()

	def canceled(self):
		self.active = False

	def dump(self, variables):
		self.window.run_command("rapid_debug_dump_variable", { 'variables': variables })

	def go(self):
		self.window.run_command("rapid_debug_run")

	def help(self):
		# TODO use a dictionary or something.
		out(
			"""The following commands are available:

				cb			Clear all breakpoints.
				d <var>		Dump expression <var>.
				g			Continue running.
				h			Show this help.
				q			Stop debugging session.
			""")

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

	def unknown(self):
		out("Unknown command; use h for help.")


class RapidDebugStopSessionCommand(sublime_plugin.WindowCommand):
	def run(self):
		send_cmd("Debug.stop()")
		editorState.stopDebugging()

		if editorState.stopped:
			self.window.run_command('rapid_debug_run')

		self.window.run_command('rapid_debug_remove_all_breakpoints')
		out("Debugger detached.")


class RapidDebugDumpVariable(sublime_plugin.WindowCommand):
	def run(self, variables=None):
		if not variables or len(variables) == 0:
			# no variable name given -> try to get it from the active view
			view = self.window.active_view()

			# get all selected regions and expand 0-length regions to cover words.
			regions = [r if r.a != r.b else view.word(r) for r in view.sel()]

			# get contents
			variables = [view.substr(r) for r in regions]
			variables = [v for v in variables if v != None and v != '']

		# still no variables? ask it from the user using an input panel
		if not variables or len(variables) == 0:
			self.window.show_input_panel(
				"Dump Expression", "",
				lambda t: self.window.run_command("rapid_debug_dump_variable", { 'variables': [t]}),
				None,
				None)
		else:
			cmds = ['Debug.dump_variable(%(var)s, "%(desc)s")' % { 'var': v, 'desc': escape_lua_string(v) } for v in variables]
			print(cmds)
			send_cmd(";".join(cmds))