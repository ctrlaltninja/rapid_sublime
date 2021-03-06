import os
import re
from unittest import TestCase
from rapid_sublime.rapid_methodcomplete import RapidCollector
from rapid_sublime.rapid_functionstorage import RapidFunctionStorage

class TestRapidCollector_FullProject(TestCase):
    def setUp(self):
        self.project = os.path.join(os.path.dirname(__file__), "project")
        RapidFunctionStorage.clear()

    def test_save_method_signatures_creates_functions_for_find(self):
        target = RapidCollector([self.project])

        target.save_method_signatures()

        # TODO this does not check the descriptions correctly
        results = sorted(list(map(
            lambda f: f.getFunction(),
            RapidFunctionStorage.getFindFunctions())))

        expected = sorted([
            'function foo1(param1, param2, ...)',
            'function bar1(param1, param2)',
            'function tbl:foo()',
            'function tbl.bar()',
            '/// foo1(x)',
            '/// function_from_header()',
            '/// r1, r2, r3, r4 = multiple_returns(cbuffer, index)',
            '/// baz,boz = foobar(x, y)',
            '/// Foo.bar(x, y)',
            '/// baz,boz = Foo.bar(x, y)',
            'function baz()',
            'function baz1(param1, param2, ...)',
            'function baz2(param1, param2)',
            '/// a1,... = variadic_return(x, y)'])

        self.assertEqual(expected, results)

    def test_get_files_in_project(self):
        target = RapidCollector([self.project])

        luaFiles = []
        cppFiles = []

        cppFilePattern = None
        excludedFolders = []
        includedFolders = None

        files = target.get_files_in_project(self.project, cppFilePattern, excludedFolders, includedFolders, luaFiles, cppFiles)

        self.assertEqual(2, len(luaFiles))

        # .h files are included in the search, so two results:
        self.assertEqual(2, len(cppFiles))