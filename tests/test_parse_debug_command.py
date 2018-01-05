from unittest import TestCase
from rapid_sublime.rapid_debug import Command
from rapid_sublime.rapid_debug import parse_debug_command

class Test_parse_debug_command(TestCase):
	def test_parse_no_parameter(self):
		cases = {
			'cb'	: (Command.REMOVE_ALL_BREAKPOINTS, None),
			'cb '	: (Command.REMOVE_ALL_BREAKPOINTS, None),
			'g'		: (Command.RUN, None),
			'idle'	: (Command.IDLE, None),
			'q'		: (Command.STOP, None),

			' cb '	: (Command.UNKNOWN, None),
			'foo'	: (Command.UNKNOWN, None),
			''		: (Command.UNKNOWN, None),
		}

		for case in cases:
			self.assertEqual(cases[case], parse_debug_command(case), "Case <" + case + ">")

	def test_parse_parameters(self):
		cases = {
			'd var1': (Command.DUMP, ["var1"]),
			'd var1  ': (Command.DUMP, ["var1"]),
		}

		for case in cases:
			self.assertEqual(cases[case], parse_debug_command(case), "Case <" + case + ">")
