class _EditorState(object):
	def __init__(self):
		self.stopped = False
		self.debugging = False

	def breakIntoDebugger(self):
		self.stopped = True

	def run(self):
		self.stopped = False

	def stopDebugging(self):
		self.debugging = False

	def startDebugging(self):
		self.debugging = True

editorState = _EditorState()