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

- fix static analysis / LuaCheck
- continuous testing support a'la NCrunch
- investigate using regions / phantoms on RapidOutputView to colorize helps and make them easier to read
- Refactoring ideas:
	- strip /// and whitespace already when scanning files from RapidCollector
	- make autocomplete and helps just use one data structure
	- share implementation of save_method_signature and save_method_signature (only Lua part for now)
	- rename save_method_signature - it is actually actually saving many signatures for a single file
	- rename RapidOutputView.printMessage to just print
	- get rid of repeating "Rapid" on classnames. It bears no information.
	- rename rapid_parse.py to rapid_settings.py
	- remove HLSL support, we are not using it anyway and it does not probably work
	- define protocol between Shinobi / editor a bit more precisely
- proper lua parser

- Debugger
    - visualize current line with background color
    - show a special icon when the current line is on a line with breakpoint
    - fix bug: still doesn't show current line marker for newly opened views
    - dump upvalues

    - start debugging when setting breakpoint
    - keyboard shortcut for focusing to debug input: pause/break
    - traceback dump

    - improve dump variable
        - parsing of DUMPV messages
        - improve context checking so that it can parse things like config.width without selecting it all
        - set options dynamically
            - how many levels
            - how to limit long arrays
        - dumping arrays: d array,5 -> dumps 5 first indexes (even if they are not there :)
    - modify Serpent to print "-- ..." when stopping based on maxnum
    - list breakpoints
    - syncing breakpoints between editor and Shinobi
        - when starting with F5
        - CTRL+R ?
    - step over
        - break when stack depth returns to the same
    - step out
        - break when stack depth is reduced by one
    - do something to the #ATLINE , they are fugly
    - visualize variable values using Sublime's Phantoms / on hover
    - breaking on error and assert
        - assumption: you are not able to correct the situation from the debugger, but just inspect state
        - if debugging is on, call debug loop function directly from error?
    - traceback window?
        - own scratch window, updated each time the debug hook is hit
    - watches?
        - own scratch window, updated each time the debug hook is hit