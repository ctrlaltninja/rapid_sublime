import sublime
import sys
from unittest import TestCase
from unittest.mock import patch

# for testing sublime command
class TestRestartGameFromRoomCommand(TestCase):

    def setUp(self):
        self.view = sublime.active_window().new_file()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

    def setText(self, string):
        self.view.run_command("insert", {"characters": string})

    def verify(self, room_name, connection):
        # place the cursor before room_name
        r = self.view.find(room_name, 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(r.begin(), r.begin()))

        self.view.run_command("rapid_restart_game_from_room")

        template = '@:1\nrestart_game("c:/game/data/levels/level.level","{0}");shb_bring_to_front(g.window);'
        connection.sendString.assert_called_with(template.format(room_name))

    @patch('rapid_sublime.rapid.get_filename')
    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_multiline(self, connection, get_filename):
        get_filename.return_value = r"c:\game\data\levels\level.lua"

        self.setText("""
            def_room { name = "room1" }
            def_room { name = "room2" }

            def_roomi { name = "invalid" }

            def_room { name = "room3" }

            def_room
            {
                name = "room4"
            }

            def_room
            {
                name = "room5",
                child = {
                    nested = {
                        content = true
                    }
                },
            }

            """)

        # TODO a nested name attribute
        self.verify("room1", connection)
        self.verify("room2", connection)
        self.verify("room3", connection)
        self.verify("room4", connection)
        self.verify("room5", connection)

    @patch('rapid_sublime.rapid.get_filename')
    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_valid_single_line_all_selected(self, connection, get_filename):
        get_filename.return_value = r"/game/data/levels/level.lua"

        self.setText("""def_room{ name = "room_name", on_init_room = function(map) end, }""")

        # select the whole document
        self.view.sel().add(sublime.Region(0, self.view.size()))

        self.view.run_command("rapid_restart_game_from_room")
    
        connection.sendString.assert_called_with("""@:1\nrestart_game("/game/data/levels/level.level","room_name");shb_bring_to_front(g.window);""")

    @patch('rapid_sublime.rapid.get_filename')
    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_valid_single_line_empty_selection_after_name(self, connection, get_filename):
        get_filename.return_value = r"/game/data/levels/level.lua"
        self.setText("""def_room{ name = "room_name", on_init_room = function(map) end, }""")

        # place the cursor before room_name
        r = self.view.find('on_init_room', 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(r.begin(), r.begin()))

        self.view.run_command("rapid_restart_game_from_room")
    
        connection.sendString.assert_called_with("""@:1\nrestart_game("/game/data/levels/level.level","room_name");shb_bring_to_front(g.window);""")

    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_no_name_empty_selection(self, connection):
        self.setText("""def_room{ xxx=yyy }""")

        # place the cursor before xxx
        r = self.view.find('xxx', 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(r.begin(), r.begin()))

        self.view.run_command("rapid_restart_game_from_room")
    
        self.assertFalse(connection.sendString.called)

    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_no_def_room_empty_selection(self, connection):
        self.setText("""def_roomi { name="xyz" }""")

        # place the cursor before xxx
        r = self.view.find('xyz', 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(r.begin(), r.begin()))

        self.view.run_command("rapid_restart_game_from_room")
    
        self.assertFalse(connection.sendString.called)
