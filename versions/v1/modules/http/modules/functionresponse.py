
import sys, getopt, imp, traceback
import calendar, datetime

from modules.baseclass import *

class FunctionResponse(BaseClass):
	
	def __init__(self, response=HTTP_OK, mimetype=None, content=None, release=True, isbinary=False):
		self.response = response
		self.mimetype = mimetype
		self.release = release
		self.content = content
		self.compressed = False
		self.lastmodified = None
		self.isbinary = isbinary
		self.cachetype = "public"
