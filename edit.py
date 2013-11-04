# edit.py
# buffer editing for both ST2 and ST3 that "just works"

#Copyright (c) 2013 Ryan Hileman

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import inspect
import sublime
import sublime_plugin

try:
    sublime.edit_storage
except AttributeError:
    sublime.edit_storage = {}

def run_callback(func, *args, **kwargs):
    spec = inspect.getfullargspec(func)
    if spec.args or spec.varargs:
        return func(*args, **kwargs)
    else:
        return func()


class EditFuture:
    def __init__(self, func):
        self.func = func

    def resolve(self, view, edit):
        return self.func(view, edit)


class EditStep:
    def __init__(self, cmd, *args):
        self.cmd = cmd
        self.args = args

    def run(self, view, edit):
        if self.cmd == 'callback':
            return run_callback(self.args[0], view, edit)

        funcs = {
            'insert': view.insert,
            'erase': view.erase,
            'replace': view.replace,
        }
        func = funcs.get(self.cmd)
        if func:
            args = self.resolve_args(view, edit)
            func(edit, *args)

    def resolve_args(self, view, edit):
        args = []
        for arg in self.args:
            if isinstance(arg, EditFuture):
                arg = arg.resolve(view, edit)
            args.append(arg)
        return args


class Edit:
    def __init__(self, view):
        self.view = view
        self.steps = []

    def __nonzero__(self):
        return bool(self.steps)

    @classmethod
    def future(cls, func):
        return EditFuture(func)

    @classmethod
    def defer(cls, view, func):
        with Edit(view) as edit:
            edit.callback(func)

    def step(self, cmd, *args):
        step = EditStep(cmd, *args)
        self.steps.append(step)

    def insert(self, point, string):
        self.step('insert', point, string)

    def erase(self, region):
        self.step('erase', region)

    def replace(self, region, string):
        self.step('replace', region, string)

    def callback(self, func):
        self.step('callback', func)

    def reselect(self, pos):
        def select(view, edit):
            region = pos
            if hasattr(pos, '__call__'):
                region = run_callback(pos, view)

            if isinstance(region, int):
                region = sublime.Region(region, region)
            elif isinstance(region, (tuple, list)):
                region = sublime.Region(*region)

            view.sel().clear()
            view.sel().add(region)

        self.callback(select)

    def append(self, text):
        self.insert(self.view.size(), text)

    def run(self, view, edit):
        read_only = False
        if view.is_read_only():
            read_only = True
            view.set_read_only(False)

        for step in self.steps:
            step.run(view, edit)

        if read_only:
            view.set_read_only(True)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        view = self.view
        if sublime.version().startswith('2'):
            edit = view.begin_edit()
            self.run(edit)
            view.end_edit(edit)
        else:
            key = str(hash(tuple(self.steps)))
            sublime.edit_storage[key] = self.run
            view.run_command('apply_edit', {'key': key})


class apply_edit(sublime_plugin.TextCommand):
    def run(self, edit, key):
        sublime.edit_storage.pop(key)(self.view, edit)
