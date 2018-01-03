import os
import re
from unittest import TestCase
from rapid_sublime.rapid_find import findClass
from rapid_sublime.rapid_functionstorage import RapidFunctionStorage
from rapid_sublime.rapid_methodcomplete import RapidCollector

class TestFindClass(TestCase):
    def setUp(self):
        # collect method signatures to cache
        RapidFunctionStorage.clear()
        project = os.path.join(os.path.dirname(__file__), "project")
        collector = RapidCollector([project], [])
        collector.save_method_signatures()

    def test_basic_pattern(self):
        results = sorted(list(map(lambda r: r[0], findClass("foo.bar"))))

        expected = sorted(['Foo.bar(x, y)', 'baz,boz = Foo.bar(x, y)'])
        self.assertEqual(expected, results)

    def test_leading_star(self):
        results = sorted(list(map(lambda r: r[0], findClass("*.bar"))))

        expected = sorted(['Foo.bar(x, y)', 'baz,boz = Foo.bar(x, y)', 'function tbl.bar()'])
        self.assertEqual(expected, results)

    def test_callsite_partial_pattern_not_found(self):
        results = sorted(list(map(lambda r: r[0], findClass("tbl.ba", True))))

        self.assertEqual([], results)

    def test_callsite_exact_pattern_found(self):
        results = sorted(list(map(lambda r: r[0], findClass("tbl.bar", True))))

        expected = sorted(['function tbl.bar()'])
        self.assertEqual(expected, results)