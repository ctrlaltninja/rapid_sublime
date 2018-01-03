Bugs
----

- pressing f1 on this line crashes:
	static int shb_create_engine_systems(lua_State* L)

- Create new (lua) function with only one indented line -> no folding marker appears

- Create new (lua) function with two or more indeted lines -> folding marker appears, but cursor is thrown in the beginning of the document
	- These seem to be limitations in ST3, not easy (or even possible?) to fix by plugin code?

- Mouse folding does not work like alt+f 
	- Not possible at the moment, this is a ST3 limitation?

TODO
----

- Debugger
- investigate using regions on RapidOutputView to colorize helps and make them easier to read
- Refactoring ideas:
	- strip /// and whitespace already when scanning files from RapidCollector
	- make autocomplete and helps just use one data structure
	- share implementation of save_method_signature and save_method_signature (only Lua part for now)
	- rename save_method_signature - it is actually actually saving many signatures for a single file
	- rename RapidOutputView.printMessage to just print
	- get rid of repeating "Rapid" on classnames. It bears no information.