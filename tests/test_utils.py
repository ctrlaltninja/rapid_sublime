import os
import re
from unittest import TestCase
from rapid_sublime.rapid_utils import escape_filename

class Test_escape_filename(TestCase):
    def test_replaces_backslashes_with_forward_slashes(self):
        self.assertEqual("C:/foobar/baz.txt", escape_filename("C:\\foobar\\baz.txt"))

    def test_replaces_quotes_with_escaped_quotes(self):
        self.assertEqual(r'C:/foo \"bar\"/baz.txt', escape_filename("C:/foo \"bar\"/baz.txt"))
