import sublime, sublime_plugin

class Method:
	_name = ""
	_signature = ""
	_filename = ""
	
	def __init__(self, name, signature, filename):
		self._name = name
		self._signature = signature
		self._filename = filename

	def __repr__(self):
		return "Method(_filename: '%s', _name: '%s', _signature: '%s')" % (self._filename, self._name, self._signature)

	#function name
	def name(self):
		return self._name

	#function parameters
	def signature(self):
		return self._signature
  
  	#filename
	def filename(self):
		return self._filename

class FunctionDefinition:
	_function = ""
	_description = None

	def __init__(self, function):
		self._function = function

	def addDescription(self, desc):
		if self._description:
			self._description = self._description + "\n" + desc
		else:
			self._description = desc

	def getFunction(self):
		return self._function

	def getDescription(self):
		return self._description

class RapidFunctionStorage():
	#autocomplete (ctrl+space)
	funcs = {}

	#find (f1)
	findFuncMap = {}
	findFuncs = []

	#static analyzation (ctrl+f10)
	luaFiles = []

	# TODO remove static methods, use dependency injection where needed
	# Create a service locator (just globals) for sublime commands that need these

	@staticmethod
	def clear():
		funcs = {}
		findFuncMap = {}
		findFuncs = []
		luaFiles = []		

	@staticmethod
	def addAutoCompleteFunctions(functions, filename):
		RapidFunctionStorage.funcs[filename] = functions

	@staticmethod
	def removeAutoCompleteFunctions(filename):
		if filename in RapidFunctionStorage.funcs:
			del RapidFunctionStorage.funcs[filename]

	@staticmethod
	def getAutoCompleteList(word):
		autocomplete_list = []
		for key in RapidFunctionStorage.funcs:
			functions = RapidFunctionStorage.funcs[key]
			for method_obj in functions:
				if word.lower() in method_obj.name().lower():
					
					# parse method variables so that they can be tabbed through
					variables = method_obj.signature().split(", ")
					signature = ""
					index = 1
					for variable in variables:
						signature = signature + "${"+str(index)+":"+variable+"}"
						if index < len(variables):
							signature = signature + ", "
						index = index+1

					method_str_to_show = method_obj.name() + '(' + method_obj.signature() +')'
					method_str_to_append = method_obj.name() + '(' + signature + ')'
					method_file_location = method_obj.filename()

					autocomplete_list.append((method_str_to_show + '\t' + method_file_location, method_str_to_append))
		return autocomplete_list	

	@staticmethod
	def addLuaFile(full_path):
		if not full_path in RapidFunctionStorage.luaFiles:
			RapidFunctionStorage.luaFiles.append(full_path)
	
	@staticmethod
	def addFindFunctions(functions, filename):
		RapidFunctionStorage.findFuncMap[filename] = functions
		if RapidFunctionStorage.findFuncs:
			# clear findFuncs list in order to parse all new funcs in getFindFunctions()
			print("deleting findFuncs list... (should parse everything on next getFindFunctions() call")
			del RapidFunctionStorage.findFuncs[:]

	@staticmethod
	def removeFindFunctions(filename):
		if filename in RapidFunctionStorage.findFuncMap:
			del RapidFunctionStorage.findFuncMap[filename]
			del RapidFunctionStorage.findFuncs[:]

	@staticmethod
	def getFindFunctions():
		#parse functions again only if they have been updated, otherwise just return findFuncs list
		if not RapidFunctionStorage.findFuncs:
			if len(RapidFunctionStorage.findFuncMap) > 0:
				for key in RapidFunctionStorage.findFuncMap:
					funcs = RapidFunctionStorage.findFuncMap[key]
					for func in funcs:
						RapidFunctionStorage.findFuncs.append(func)
			else:
				print("rapid_functionstorage.py: INTERNAL ERROR: findFuncMap length is 0!")
		return RapidFunctionStorage.findFuncs

