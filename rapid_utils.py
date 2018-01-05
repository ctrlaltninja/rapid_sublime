import os
import re
import sublime

# the Sublime region key for the current row marker for the debugger
CURRENT_REGION_KEY = "current"

# the icon to place in the gutter for the current row
CURRENT_REGION_ICON = "Packages/rapid_sublime/icons/current_line.png"


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


def clear_current_row_icons():
	# clear the markers from all open files
	for window in sublime.windows():
		for view in window.views():
			view.erase_regions(CURRENT_REGION_KEY)


def focus_current_row(filename, row):
	clear_current_row_icons()

	# open file location
	success, err = open_file_location(filename, row)

	if success:
		# show current row in gutter
		view = sublime.active_window().active_view()

		# I wonder why a copy of the selection is needed:
		regions = [s for s in view.sel()]
		view.add_regions(CURRENT_REGION_KEY, regions, "mark", CURRENT_REGION_ICON, sublime.HIDDEN)

	return success, err


# TODO rename to parse_debug_message
def parseDebugMessage(cmd):
	# perhaps convert this to a function with no side-effects and make the callsite
	# do the dispatching based on the result value?
	matches = re.match('#ATLINE (.*):(.*)', cmd)

	if matches:
		filename = matches.group(1)
		row = matches.group(2)

		return focus_current_row(filename, row)

	return True, None