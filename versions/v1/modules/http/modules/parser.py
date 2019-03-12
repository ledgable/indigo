
import re
import os
import glob
import hashlib
import uuid
import copy
import urllib
import socket
import socketserver
import calendar, datetime
import contextlib

import string, cgi, time
import threading
import json
import ssl
import base64

from operator import itemgetter

from modules.baseclass import *
from modules.singleton import *
from modules.repeater import *
from .resourcemanager import *

#####################################
####
####  Runtime Content Parser
####
#####################################

contentParser = re.compile("<py>(.*?)\</py>", re.IGNORECASE | re.VERBOSE | re.DOTALL)
includeParser = re.compile("<pyinclude>(.*?)\</pyinclude>", re.IGNORECASE | re.VERBOSE | re.DOTALL)

varConditioner = re.compile("<pyif (.*?)\</pyif>", re.IGNORECASE | re.VERBOSE | re.DOTALL)
varRepeater = re.compile("<pyrepeat (.*?)\</pyrepeat>", re.IGNORECASE | re.VERBOSE | re.DOTALL)
varInnerConditions = re.compile("condition=\"(.*?)\">", re.IGNORECASE | re.VERBOSE | re.DOTALL)
varInnerCount = re.compile("count=\"(.*?)\">", re.IGNORECASE | re.VERBOSE | re.DOTALL)


@contextlib.contextmanager
def stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = io.StringIO()
		sys.stdout = stdout
		yield stdout
		sys.stdout = old

class Parser(BaseClass, metaclass=Singleton):
	
	def __init__(self):
		pass
				
	def parseRepeats(self, sessionState, content, appVars=None):
		
		content_ = re.findall(varRepeater, content);
		
		if len(content_) > 0:
			
			for found_ in content_:
				
				try:
					out_ = ""
					conditioncount_ = re.findall(varInnerCount, found_);
					start_ = 0
					end_ = 0
					
					if (conditioncount_ != None) and (len(conditioncount_) == 1):
						
						parts_ = conditioncount_[0].split(',')
						
						if len(parts_) == 0:
							pass
						
						elif len(parts_) == 1:
							end_ = int(parts_[0])
						
						elif len(parts_) == 2:
							start_ = int(parts_[0])
							end_ = int(parts_[1])
				
					inner_ = found_[(10 + len(conditioncount_[0]))::]
					
					if (end_ > 0):
						for counter_ in range(start_, end_):
							out_ += inner_.replace("%counter%", str(counter_))
			
				except Exception as inst:
					self.logException(inst)
				
				finally:
					actual_ = ("<pyrepeat%s</pyrepeat>" % found_)
					content = content.replace(actual_, out_)

		return content
			
	def parseConditionals(self, sessionState, content, appVars=None):

		content_ = re.findall(varConditioner, content);

		if len(content_) > 0:
	
			for found_ in content_:
		
				try:
					out_ = ""
					conditionresults_ = re.findall(varInnerConditions, found_);
					result_ = False
					
					if (conditionresults_ != None) and (len(conditionresults_) == 1):
						result_ = eval(conditionresults_[0], {"self":sessionState, "vars":appVars, "SECURE":RawVars().secure})
				
					inner_ = found_[(15 + len(conditionresults_[0]))::]
					conditionelse_ = inner_.find("<pyelse>")
					
					if conditionelse_ == -1:
						if result_:
							out_ = inner_
					else:
						if result_:
							out_ = inner_[:conditionelse_:]
						else:
							out_ = inner_[conditionelse_+8:]
			
				except Exception as inst:
					self.logException(inst)
				
				finally:
					actual_ = ("<pyif%s</pyif>" % found_)
					content = content.replace(actual_, out_)

		return content
	
	def parseIncludes(self, sessionState, content, appVars=None):
	
		searcher_ = re.findall(includeParser, content);
		code_locals = {}
	
		if len(searcher_) > 0:
		
			for found_ in searcher_:
				out_ = None
				
				try:
					out_ = self.loadContent(sessionState, found_, appVars, "")

				except Exception as inst:
					self.logException(inst)
				
				finally:
					actual_ = ("<pyinclude>%s</pyinclude>" % found_)
					if (out_ != None):
						content = content.replace(actual_, out_)
					else:
						content = content.replace(actual_, "")

		return content

	def parseContent(self, sessionState, content, appVars=None):

		searcher_ = re.findall(contentParser, content);
		code_locals = {}
		
		if len(searcher_) > 0:
			
			for found_ in searcher_:
				out_ = ""
				
				try:
					with stdoutIO() as s:
						toExecute_ = str(found_)
						code_globals = {"self":sessionState, "vars":appVars, "stdout":s}
						exec(toExecute_, code_globals, code_locals)
					
					out_ = s.getvalue()[:-1:]
				
				except Exception as inst:
					self.logException(inst)
				
				finally:
					actual_ = ("<py>%s</py>" % found_)
					content = content.replace(actual_, out_)
	
		return content

	def loadContent(self, sessionState, filename=None, appVars=None, root="views"):
	
		if (filename == None):
			return ""
		
		#realRoot_ = "%s/%s" % (sessionState.handler.DIRECTORY, root)
		#realRoot_ = "sites/%s/%s" % (appVars.site, root)
		
		newContent_, compressed_, modified_, size_ = sessionState.handler.RESOURCES.resourceForUrl(("%s/%s" % (root, filename)))
		
		if (newContent_ != None):
			extension_ = os.path.splitext(filename)[1][1:]
			
			if (extension_ == "py"):
				newContent_ = self.parseConditionals(sessionState, newContent_, appVars)
				newContent_ = self.parseRepeats(sessionState, newContent_, appVars)
				newContent_ = self.parseIncludes(sessionState, newContent_, appVars)
				newContent_ = self.parseContent(sessionState, newContent_, appVars)
		else:
			self.log("Cannot find content for %s" % filename)
		
		return newContent_

	def appendView(self, sessionState, viewName=None, content=None, appVars=None):
	
		if (viewName == None):
			return ""
		
		newContent_, compressed_, modified_, size_ = sessionState.handler.RESOURCES.resourceForUrl("%s/%s" % ("views", viewName))
		
		try:
			if (newContent_ != None):
				newContent_ = self.parseConditionals(sessionState, newContent_, appVars)
				newContent_ = self.parseRepeats(sessionState, newContent_, appVars)
				newContent_ = self.parseIncludes(sessionState, newContent_, appVars)
				newContent_ = self.parseContent(sessionState, newContent_, appVars)
			
			if (content != None) and (newContent_ != None):
				newContent_ = newContent_.replace("%%content%%", content)
	
		except Exception as inst:
			self.logException(inst)

		return newContent_
