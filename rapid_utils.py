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
	else:
		RapidOutputView.printMessage(file_name + " not found in the project folders!")


def escape_filename(filename):

	return filename.replace("\\", "/").replace('"', r'\"')