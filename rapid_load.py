import sublime

from .rapid_output import RapidOutputView
from .rapid import RapidConnectionThread
from .rapid_parse import RapidSettings

def plugin_loaded():
	# Run a command to start collecting help data soon after Sublime has started
	view = sublime.active_window().active_view()
	sublime.set_timeout(lambda: view.run_command('rapid_start_collector'), 2000)

	if RapidSettings().isAutoConnectEnabled():
		# Start a thread for handling the connection to the rapid server
		RapidConnectionThread.checkConnection()

	print("Rapid: plugin loaded.")

def plugin_unloaded():
	RapidConnectionThread.killConnection()
	print("Rapid: plugin unloaded.")
