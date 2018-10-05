
import re
import os
import glob
import hashlib
import uuid
import urllib
import socket
import socketserver
import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import base64

from threading import Thread
from operator import itemgetter

from modules.baseclass import *
from modules.singleton import *
from modules.repeater import *
from modules.daoobject import *

#####################################
####
####  Runtime Security Manager
####
#####################################

class SecurityMgr(BaseClass):

	realms_ = None

	def load(self):
	
		requestedPath_ = os.path.normpath("%s/%s" % (self.directory_, "config/permissions.txt"))
	
		if (os.path.exists(requestedPath_)):
	
			with open(requestedPath_, 'r', encoding=UTF8) as fileConfig:
				
				realm_ = "basic"
				
				for line_ in fileConfig:
				
					permissions_ = None
					
					if (realm_ in self.realms_):
						permissions_ = self.realms_[realm_]
					else:
						permissions_ = {}
						self.realms_[realm_] = permissions_

					try:
						
						if (line_[-1::] == "\n"):
							line_ = line_[:-1:]
								
						if (line_ != ""):
							
							if (line_[0:1] == "["):
								realm_ = line_[1:-1].lower()
						
							elif (line_[0:1] == "#"):
								pass # ignore - comment
							
							else:
								parts_ = line_.split("=")
								auth_ = parts_[0].split(":")
								access_ = parts_[1].split(",")

								userinfo_ = DAOObject({})
								
								setattrs(userinfo_,
									username = auth_[0].lower(),
									password = auth_[1].lower(),
									rights = access_
									)

								permissions_[userinfo_.username] = userinfo_

					except Exception as inst:
						self.logException(inst)

	def check(self, header=None):
	
		parts_ = None
		
		if (header != None):
			parts_ = header.split(" ", 1)
		
		try:
			realm_ = "basic"
			
			if (parts_ != None):
				realm_ = parts_[0].lower()

			permissions_ = None
			
			if (realm_ in self.realms_):
				permissions_ = self.realms_[realm_]

			else:
				self.log("Unknown realm - %s" % realm_)
				return False, None, []

			if (permissions_ != None):
				
				allusers_ = list(permissions_.keys())

				if (parts_ != None) and (len(parts_) == 2):
				
					todecode_ = parts_[1]
					decoded_ = base64.b64decode(todecode_).decode(UTF8)
					userinfo_ = decoded_.split(":")
										
					username_ = userinfo_[0].lower()
					passwordtoken_ = userinfo_[1].lower()
					
					if (username_ in allusers_):
						userinfo_ = permissions_[username_]
						
						if (userinfo_.password == passwordtoken_):
							return True, username_, userinfo_.rights
						else:
							return False, None, []
				
					else:
						return False, None, []
						
				if ("*" in allusers_):
					userinfo_ = permissions_["*"]
					return True, "*", userinfo_.rights

		except Exception as inst:
			self.logException(inst)

		return False, None, []

	def __init__(self, directory):
		
		self.directory_ = directory
		self.realms_ = {}
		
		self.log("Created instance of security manager")

		self.load()
