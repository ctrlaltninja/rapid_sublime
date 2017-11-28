import re
from unittest import TestCase
from rapid_sublime.rapid import parse_room_filename

class TestParseRoomFilename(TestCase):
    def test_slashes_returns_names(self):
        world, level = parse_room_filename('data/worlds/world1/level1.lua')

        self.assertEqual("world1", world)
        self.assertEqual("level1", level)

    def test_backslashes_returns_names(self):
        world, level = parse_room_filename(r'c:\foo\worlds\world1\level1.lua')

        self.assertEqual("world1", world)
        self.assertEqual("level1", level)

    def test_invalid_returns_none(self):
        world, level = parse_room_filename('level1.lua')

        self.assertEqual(None, world)
        self.assertEqual(None, level)