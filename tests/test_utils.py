import os
import re
from unittest import TestCase
from rapid_sublime.rapid_utils import escape_filename
from rapid_sublime.rapid_utils import escape_lua_string

class Test_escape_filename(TestCase):
	def test_replaces_backslashes_with_forward_slashes(self):
		self.assertEqual("C:/foobar/baz.txt", escape_filename("C:\\foobar\\baz.txt"))

	def test_replaces_quotes_with_escaped_quotes(self):
		self.assertEqual(r'C:/foo \"bar\"/baz.txt', escape_filename("C:/foo \"bar\"/baz.txt"))

class Test_escape_lua_string(TestCase):
	def test_replaces_backslashes_with_forward_slashes(self):

		cases = {
			'simple': 'simple',
			'"quotes"': r'\"quotes\"',
			"'quotes'": r"\'quotes\'",
			"line\nbreak": 'line\\nbreak',
		}

		for case in cases:
			self.assertEqual(cases[case], escape_lua_string(case))