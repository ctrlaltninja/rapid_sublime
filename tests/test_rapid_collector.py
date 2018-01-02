import os
import re
from unittest import TestCase
from rapid_sublime.rapid_methodcomplete import RapidCollector

class TestRapidCollector_FullProject(TestCase):
    def setUp(self):
        self.project = os.path.join(os.path.dirname(__file__), "project")

    def test_save_method_signatures(self):
        target = RapidCollector("project", [])

        target.save_method_signatures()

        # TODO
        self.assertEqual(True, True)

    def test_get_files_in_project(self):
        target = RapidCollector("project", [])

        luaFiles = []
        cppFiles = []

        files = target.get_files_in_project(self.project, luaFiles, cppFiles)

        self.assertEqual(2, len(luaFiles))

        # .h files are not included in the search, so only one result:
        self.assertEqual(1, len(cppFiles))
