import os
import re
from unittest import TestCase
from rapid_sublime.rapid_find import find
from rapid_sublime.rapid_functionstorage import RapidFunctionStorage
from rapid_sublime.rapid_methodcomplete import RapidCollector

class TestFind(TestCase):
    def setUp(self):
        # collect method signatures to cache
        RapidFunctionStorage.clear()
        project = os.path.join(os.path.dirname(__file__), "project")
        collector = RapidCollector([project], [])
        collector.save_method_signatures()

    def test_basic_pattern(self):
        results = sorted(list(map(lambda r: r[0], find("foo1"))))

        expected = sorted(['foo1(x)', 'function foo1(param1, param2, ...)'])
        self.assertEqual(expected, results)

    def test_methods(self):
        results = sorted(list(map(lambda r: r[0], find("bar"))))

        expected = sorted([
            'Foo.bar(x, y)',
            'baz,boz = Foo.bar(x, y)',
            'baz,boz = foobar(x, y)',
            'function bar1(param1, param2)',
            'function tbl.bar()'])
        
        self.assertEqual(expected, results)

    def test_leading_wildcard(self):
        results = sorted(list(map(lambda r: r[0], find("*o1"))))

        expected = sorted(['foo1(x)', 'function foo1(param1, param2, ...)'])
        self.assertEqual(expected, results)
    
    def test_case_difference(self):
        results = sorted(list(map(lambda r: r[0], find("Foo"))))

        expected = sorted([])
        self.assertEqual(expected, results)

    def test_descriptions_are_not_matched(self):
        results = sorted(list(map(lambda r: r[0], find("blabla"))))

        expected = sorted([])
        self.assertEqual(expected, results)