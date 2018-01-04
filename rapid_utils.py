import os
import re
import sublime

def open_file_location(file_name, row):
	window_found = sublime.active_window()
	path = None

	# scan all opened folders of *all* windows
	# we need scan other windows, because the rapid output view
	# can be detached from the window, where the project is loaded
	for window in sublime.windows():
		for folder in window.folders():
			candidate = os.path.join(folder, file_name)
			if os.path.isfile(candidate):
				window_found = window
				path = candidate
				break

	if path == None:
		# exact match was not found. Try recursing the subdirectories of folders opened in Sublime
		for window in sublime.windows():
			for folder in window.folders():
				for root, subfolders, files in os.walk(folder):
					for subfolder in subfolders:
						candidate = os.path.join(root, subfolder, file_name)
						if os.path.isfile(candidate):
							window_found = window
							path = candidate
							break

	if path != None:
		view = window_found.find_open_file(path)
		if view != None:
			window_found.focus_view(view)
		else:
			window_found.focus_group(0)
		view = window_found.open_file(path + ":" + str(row), sublime.ENCODED_POSITION)
		return (True, None)
	else:
		return (False, "%(file)s not found in project folders." % { 'file': file_name })


def escape_filename(filename):
	return filename.replace("\\", "/").replace('"', r'\"')


def parseDebugMessage(cmd):
	matches = re.match('#ATLINE (.*):(.*)', cmd)
	if matches:
		filename = matches.group(1)
		line = matches.group(2)

		success, err = open_file_location(filename, line)

		if success:
			# show current line in gutter
			view = sublime.active_window().active_view()
			region = [s for s in view.sel()]
			icon = "Packages/rapid_sublime/icons/current_line.png"
			view.add_regions("current", region, "mark", icon, sublime.HIDDEN)

		return success, err