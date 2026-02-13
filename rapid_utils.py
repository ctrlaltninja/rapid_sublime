import os
import re
import sublime
from rapid_sublime.rapid_base import editorState

# the Sublime region key for the current row marker for the debugger
CURRENT_REGION_KEY = "current"

# the icon to place in the gutter for the current row
CURRENT_REGION_ICON = "Packages/rapid_sublime/icons/current_line.png"


def open_file_location(file_name, row):
	window_found = sublime.active_window()
	path = None
	
	# Check first if the file is already open in any view
	for window in sublime.windows():
		for view in window.views():
			view_file_name = view.file_name()
			if view_file_name and os.path.basename(view_file_name) == file_name:
				window_found = window
				path = view_file_name
				break

	# Check if the file exist at the root of a project folder
	if path == None:
		for window in sublime.windows():
			for folder in window.folders():
				candidate = os.path.join(folder, file_name)
				if os.path.isfile(candidate):
					window_found = window
					path = candidate
					break

	# As a last resort do a (slow) recursive search in all folders
	if path == None:
		for window in sublime.windows():
			for folder in window.folders():
				# Use os.walk with topdown=True for early termination
				for root, subfolders, files in os.walk(folder, topdown=True):
					# Check if file exists in current directory's files list first
					if file_name in files:
						candidate = os.path.join(root, file_name)
						window_found = window
						path = candidate
						break
					
					# Filter out "build" directory
					subfolders[:] = [d for d in subfolders if not d.startswith('.') and d not in {'build'}]
				if path:  # Break out of folder loop
					break
			if path:  # Break out of window loop
				break

	if path != None:
		view = window_found.find_open_file(path)
		if view != None:
			window_found.focus_view(view)
		else:
			window_found.focus_group(0)
		view = window_found.open_file(path + ":" + str(row), sublime.ENCODED_POSITION)
		return True, None
	else:
		return False, "%(file)s not found in project folders." % { 'file': file_name }


def escape_filename(filename):
	return filename.replace("\\", "/").replace('"', r'\"')


def escape_lua_string(str):
	return str.replace("\n", "\\n").replace('"', r'\"').replace("'", r'\'')

def clear_region_from_all_views(region_key):
	for window in sublime.windows():
		for view in window.views():
			view.erase_regions(region_key)


def clear_current_row_icons():
	clear_region_from_all_views(CURRENT_REGION_KEY)

def _highlight_current_row():
	view = sublime.active_window().active_view()
	regions = [view.line(r) for r in view.sel()]
	view.add_regions(CURRENT_REGION_KEY, regions, "region.yellowish", CURRENT_REGION_ICON)

def focus_current_row(filename, row):
	clear_current_row_icons()

	# open file location
	success, err = open_file_location(filename, row)

	if success:
		# show current row in the gutter
		# using a timer: the view may not be opened yet and therefore
		# Sublime will just ignore it for now. So do it later.
		sublime.set_timeout(_highlight_current_row, 100)

	return success, err


def parse_debug_message(cmd):
	# perhaps convert this to a function with no side-effects and make the callsite
	# do the dispatching based on the result value?
	matches = re.match('#ATLINE (.*):(.*)', cmd)

	if matches:
		editorState.breakIntoDebugger()
		filename = matches.group(1)
		row = matches.group(2)

		return focus_current_row(filename, row)

	return True, None