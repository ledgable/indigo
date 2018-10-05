
import re
import os
import glob
import hashlib
import uuid
import urllib
import socket
import socketserver
import calendar, datetime
import zlib

import string, cgi, time
import threading
import json
import ssl
import base64

from operator import itemgetter

from modules.baseclass import *
from modules.singleton import *
from modules.repeater import *

#####################################
####
####  Runtime Resource Manager
####
#####################################

class ResourceMgr(BaseClass):
	
	timer_ = None
	
	def invalidate(self, url):
		
		if url in self.resources_.keys():
			del self.resources_[url]
	
	def poller(self, args):
	
		# perform sync event
	
		keys_ = list(self.resources_.keys())
	
		if len(keys_) > 0:
			
			for key_ in keys_:
				
				try:
					requestedPath_ = os.path.normpath("%s/%s" % (self.directory_, key_))
					(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(requestedPath_)
				
					resourceinfo_ = self.resources_[key_]
				
					if resourceinfo_["modified"] < mtime:
						self.log(("file was updated - reloading %s from os" % key_), "cache-update")
						self.resourceForUrl(key_, resourceinfo_["binary"], True)
							
				except IOError:
					pass
		
				except Exception as inst:
					self.log(("file was removed (%s)" % key_), "cache-update")
					del self.resources_[key_]

	def resourceForUrl(self, url, binary=False, reload=False):

		resourceinfo_ = None
		resources_ = list(self.resources_.keys())
		
		if (url in resources_) and (reload == False):
			resourceinfo_ = self.resources_[url]
				
		else:
			requestedPath_ = os.path.normpath("%s/%s" % (self.directory_, url))
						
			if (os.path.commonprefix([requestedPath_, self.directory_]) == self.directory_):
				
				if os.path.exists(requestedPath_):
		
					try:
						ptrToFile_ = None
						
						if binary:
							ptrToFile_ = open(requestedPath_, "rb")
						else:
							ptrToFile_ = open(requestedPath_, "r")
						
						content_ = ptrToFile_.read()
						ptrToFile_.close()
						
						(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(requestedPath_)
						
						compressed_ = None
						
						if binary:
							compressed_ = zlib.compress(content_)
						
						resourceinfo_ = {"data":content_, "modified":mtime, "size":size, "binary":binary, "compressed":compressed_}

					except IOError:
						pass
		
					except Exception as inst:
						self.logException(inst)
			
				else:
					self.log("File doesnt exist - %s" % (requestedPath_))
				
				if resourceinfo_ != None:
					self.resources_[url] = resourceinfo_
			
			else:
				self.log("Attempts to access path %s with start=%s" % (requestedPath_, self.directory_), "fileaccess")

		if resourceinfo_ != None:
			return resourceinfo_["data"], resourceinfo_["compressed"], resourceinfo_["modified"], resourceinfo_["size"]

		return None, None, 0, 0

	def __init__(self, directory_):

		self.directory_ = directory_
		self.resources_ = {}
		
		self.timer_ = Repeater(10.0, self.poller, self)
		self.timer_.start()
		
		self.log("Created instance of resource manager")
	
	@property
	def resources(self):
		return self.resources_
