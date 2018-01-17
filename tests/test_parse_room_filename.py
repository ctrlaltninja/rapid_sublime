import re
from unittest import TestCase
from rapid_sublime.rapid import parse_room_filename

class TestParseRoomFilename(TestCase):
    def test_slashes_returns_names(self):
        level = parse_room_filename('data/levels/level1.lua')

        self.assertEqual("data/levels/level1.level", level)

    def test_backslashes_returns_names(self):
        level = parse_room_filename(r'c:\foo\levels\level1.lua')

        self.assertEqual(r'c:/foo/levels/level1.level', level)

    def test_local_file_returns_name(self):
        level = parse_room_filename('level1.lua')

        self.assertEqual("level1.level", level)