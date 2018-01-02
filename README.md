Rapid
=====

Collection of scripts for Sublime Text 3 to be used in [Ctrl Alt Ninja Ltd.](http://druidstone-game.com) rapid development environment.

Originally by Almost Human Ltd. This fork adds some very specific customizations.

License
-------

See [LICENSE](LICENSE).

Installation
------------

1. Install Package Control to Sublime Text if not installed.

2. Add following lines to "Package Control.sublime-settings" file:

		"repositories":
		[
			"https://github.com/ctrlaltninja/rapid_sublime"
		]

	To run the unit tests for Rapid (not needed if not developing Rapid), add the following lines:

		"repositories":
		[
			"https://github.com/ctrlaltninja/rapid_sublime",
			"https://github.com/SublimeText/UnitTesting"
		]

3. Install package "Rapid" through Package Control

4. Optional: install "UnitTesting" through Package Control

Running the Rapid Unit Tests
----------------------------

The unit tests can be run from Sublime Text through the command palette:

- UnitTesting: Test Current File
- UnitTesting: Test Current Package
- UnitTesting: Test Current Package with Coverage