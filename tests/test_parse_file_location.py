from unittest import TestCase
from rapid_sublime.rapid_output import parse_file_location

class TestParseFileLocation(TestCase):
    def test_local_lua_file(self):

        cases = [
            "#ATLINE C:/jp/shinobi/lua/patch_func.lua:22",
            "C:/jp/shinobi/lua/fwk.lua:49: in function <C:/jp/shinobi/lua/fwk.lua:44>",
            "main.lua:198: missions.lua:3: data/missions/mission_base.lua:1: unexpected symbol near '='",
            "main.lua:198: in function 'init'",
            "C:/jp/shinobi/lua/fwk.lua:42: in function 'start_app'" ]

        expected = [
            ("C:/jp/shinobi/lua/patch_func.lua", 22),
            ("C:/jp/shinobi/lua/fwk.lua", 44),
            ("data/missions/mission_base.lua", 1),
            ("main.lua", 198),
            ("C:/jp/shinobi/lua/fwk.lua", 42) ]

        for i in range(0, len(cases)):
            self.assertEqual(expected[i], parse_file_location(cases[i]))
