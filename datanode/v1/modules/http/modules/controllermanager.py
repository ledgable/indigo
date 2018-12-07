
import re
import os
import glob
import importlib.util
import types

import hashlib
import uuid
import urllib
import socket
import select
import socketserver
import concurrent.futures

import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import base64
import errno
import http.client
import sys, getopt, imp, traceback

from time import sleep

from modules.baseclass import *
from modules.repeater import *
from modules.singleton import *

NEW_LINE = "\r\n"

class HTTPController(BaseClass):

	pass

class HTTPApplication(BaseClass):

	manager_ = None

	@property
	def handler(self):
		if (self.manager_ != None):
			return self.manager_.manager
		return None

	@property
	def manager(self):
		return self.manager_

	def __init__(self, manager):
		self.manager_ = manager


class Definition(BaseClass):
	
	def __init__(self, hidden, tracksession, auth, method, controller, function, regx, description, weight=0, site="*"):
		
		self.controller_ = controller
		self.hidden_ = int(hidden)
		
		if auth != None and auth != "":
			self.auth_ = auth.split(",")
		else:
			self.auth_ = None
		
		self.method_ = method
		self.function_ = function
		self.regx_ = regx
		self.site_ = site
		self.compiled_ = re.compile(regx, re.IGNORECASE | re.VERBOSE)
		self.description_ = description
		self.tracksession_ = int(tracksession)
		self.weight_ = weight
		self.attrs_ = None
		self.niceregx_ = None
	
	@property
	def site(self):
		return self.site_
	
	@property
	def regx(self):
		return self.regx_
	
	@property
	def method(self):
		return self.method_
	
	@property
	def sortedAttrs(self):
		
		if (self.attrs_ == None):
			attrs_ = getattr(self.compiled_, "groupindex")
			
			sortedattrs_ = None
			attrsout_ = []
			
			if attrs_ != None:
				sortedattrs_ = OrderedDict(sorted(attrs_.items(), key=lambda x: x[1]))
				
				for attr_ in sortedattrs_.keys():
					attrsout_.append({"attribute":attr_, "position":sortedattrs_[attr_]})
				
			self.attrs_ = attrsout_
		
		return self.attrs_

	@property
	def function(self):
		return self.function_
	
	@property
	def compiled(self):
		return self.compiled_
	
	@property
	def niceregx(self):
		
		if (self.niceregx_ == None):
			niceregx_ = self.regx_.replace("[^-&*/\%]*", "")
			niceregx_ = niceregx_.replace("[^&*/\%]*", "")
			niceregx_ = niceregx_.replace("[^/\%]*", "")
			niceregx_ = niceregx_.replace("?P", "")
			niceregx_ = niceregx_.replace("&", "&amp;")
			niceregx_ = niceregx_.replace(">", "&gt;")
			niceregx_ = niceregx_.replace("<", "&lt;")
			
			if niceregx_[0] == "^":
				niceregx_ = niceregx_[1::]
			
			self.niceregx_ = niceregx_
		
		return self.niceregx_
	
	@property
	def description(self):
		return self.description_
	
	@property
	def auth(self):
		return self.auth_
	
	@property
	def weight(self):
		return self.weight_
	
	@property
	def tracksession(self):
		return self.tracksession_
	
	@property
	def hidden(self):
		return self.hidden_
	
	@property
	def controller(self):
		return self.controller_



class RouteOut(BaseClass):
	
	def __init__(self, controller, function, vars, tracksession, auth, weight=0, regx=None, site="*"):
		self.controller_ = controller
		self.function_ = function
		self.vars_ = vars
		self.auth_ = auth
		self.weight_ = weight
		self.regx_ = regx
		self.site_ = site
		self.compiled_ = re.compile(regx, re.IGNORECASE | re.VERBOSE)
		self.tracksession_ = tracksession
	
	@property
	def auth(self):
		return self.auth_
	
	@property
	def site(self):
		return self.site_
	
	@property
	def tracksession(self):
		return self.tracksession_
	
	@property
	def weight(self):
		return self.weight_
	
	@property
	def compiled(self):
		return self.compiled_
	
	@property
	def regx(self):
		return self.regx_
	
	@property
	def controller(self):
		return self.controller_
	
	@property
	def function(self):
		return self.function_
	
	@property
	def vars(self):
		return self.vars_
	
	def __repr__(self):
		return "%s@%s %d" % (self.controller_, self.function_, self.weight_)

class AppRoutes(BaseClass):
	
	routes_ = None
	
	def __init__(self):
		self.routes_ = []
	
	def add(self, weight, hidden, tracksession, auth, qualname, method, controller, function, regex, description):
		
		# self.log("Added function %s:%s:%s" % (qualname, controller, function))
		
		newroute_ = Definition(hidden, tracksession, auth, method, controller, function, regex, description, weight)
		
		if len(self.routes_) == 0:
			self.routes_.append(newroute_)
		
		else:
			index_ = 0
			inserted_ = False
			
			for route_ in self.routes_:
				
				if route_.weight > newroute_.weight:
					# insert route here
					self.routes_.insert(index_, newroute_)
					inserted_ = True
					break
				
				index_ += 1
			
			if (inserted_ == False):
				self.routes_.append(newroute_)

	@property
	def all(self):
		return self.routes_
	
	def list(self):
		if (RawVars().debug):
			for definition in self.routes_:
				print("definition = %s" % definition)

	def match(self, string, action):
		
		if (len(self.routes_) == 0):
			return None
		
		string_ = urllib.parse.unquote(string)
		if (string_ == None) or (string_ == ""):
			string_ = "/"
		
		routefound_ = None
		
		for definition in self.routes_:
			
			try:
				result_ = None
				
				if (definition.method == action):
					result_ = re.match(definition.compiled, string_);
				
				if (result_ != None):
					routefound_ = RouteOut(definition.controller, definition.function, result_.groupdict(), definition.tracksession, definition.auth, definition.weight, definition.regx, definition.site_)
					break
			
			except Exception as inst:
				self.logException(inst)

		return routefound_


class ControllerManager(BaseClass):
	
	controllers_ = None
	applications_ = None
	manager_ = None
	
	routes_ = None
	
	@property
	def manager(self):
		return self.manager_
	
	@property
	def routes(self):
		return self.routes_
	
	@property
	def applications(self):
		return self.applications_
	
	def controllerForId(self, modulename=None):
	
		module_ = None
		
		if (modulename in self.controllers_.keys()):
			module_ = self.controllers_[modulename]
		
		return module_
	
	def loadControllerGroup(self, directory=None):
	
		if (os.path.exists(directory)):
	
			try:
				for file_ in os.listdir(directory):
					
					if (file_[0:1] != "."):
						if (file_[0:2] != "__") and (file_[-2:] == "py"):

							path_ = directory + "/" + file_
							modulename_ = file_[:-3]
							
							spec_ = importlib.util.spec_from_file_location(modulename_, path_)
							module_ = importlib.util.module_from_spec(spec_)
							
							if (module_ != None):
								
								spec_.loader.exec_module(module_)
		
								for minternal_ in inspect.getmembers(module_, inspect.isclass):
									modulefound_ = minternal_[1]
									
									if (modulefound_.__module__ == module_.__name__):
										
										if (issubclass(modulefound_, HTTPController)):
											
											self.controllers_[modulename_] = module_
											self.log("Loading Controller - %s" % file_)

											for fnname_ in dir(modulefound_):
												fn_ = getattr(modulefound_, fnname_)
												
												if (hasattr(fn_, "_decorators")):
													qualname_ = fn_.__name__
													if (fn_.__module__ == modulename_):
														decos_ = getattr(fn_, "_decorators")
														self.routes.add(decos_[0], decos_[1], decos_[2], decos_[3], qualname_, decos_[4], modulename_, fnname_, decos_[5], decos_[6])

										else:
											fnname_ = str(modulename_)
											appinstance_ = modulefound_(self)
											self.applications_[fnname_] = appinstance_
											
											self.log("Application Loaded - %s" % fnname_)

			except Exception as inst:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				trace_ = NEW_LINE.join(traceback.format_tb(exc_tb, limit=8))
				message_ = "An exception occurred = [%s:%d] - %s\r\n\r\ntrace = %s" % (self.__class__.__name__, exc_tb.tb_lineno, inst, trace_)
				self.log(message_, "critical")

	
	def __init__(self, manager=None):
		self.log("Created instance of controller manager")
		self.controllers_ = {}
		self.manager_ = manager
		self.applications_ = {}
		self.routes_ = AppRoutes()

