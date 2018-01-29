import sublime
import sys
from unittest import TestCase
from unittest.mock import patch

# for testing sublime command
class TestRapidEvalCommand(TestCase):

    def setUp(self):
        self.view = sublime.active_window().new_file()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command("close_file")

    def setText(self, string):
        self.view.run_command("insert", {"characters": string})

    @patch('rapid_sublime.rapid.RapidConnectionThread')
    def test_incorrect_indentation_does_not_cause_endless_loop(self, connection):
        self.setText(" def_room {\n\tblah1 = 1,\nblah2 = 2,\n}")

        self.view.run_command("rapid_eval")

        # The insert command above actually sends those key strokes to
        # Sublime, which does its indentation magic. That's why the
        # spaces and tabs differ.
        connection.sendString.assert_called_with("@:1\n def_room {\n \tblah1 = 1,\n \tblah2 = 2,\n \t}")