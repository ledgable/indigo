
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

from .baseclass import *
from .singleton import *
from .repeater import *
from .daoobject import *

class IPBlocker(BaseClass, metaclass=Singleton):

	realms_ = None
	seen_ = {}
	directory_ = os.path.dirname(os.path.abspath(__file__))
	
	
	def poller(self, args=None):
	
		keys_ = list(self.seen_.keys())
		
		if (len(keys_) > 0):
			now_ = self.epoch
			
			# cleanup if not seen in 60 seconds..

			for key_ in keys_:
				addressinfo_ = self.seen_[key_]
				if (addressinfo_.time < (now_-60)):
					del self.seen_[key_]


	def load(self):
	
		requestedPath_ = os.path.normpath("%s/../%s" % (self.directory_, "config/ipwhitelist.txt"))
	
		if (os.path.exists(requestedPath_)):
		
			with open(requestedPath_, 'r', encoding=UTF8) as fileConfig:
			
				realm_ = "all"
				
				for line_ in fileConfig:
					
					addresses_ = None
					
					if (realm_ in self.realms_):
						addresses_ = self.realms_[realm_]
					else:
						addresses_ = {}
						self.realms_[realm_] = addresses_
				
					try:
						if (line_[-1::] == "\n"):
							line_ = line_[:-1:]
					
						if (line_ != ""):
							
							if (line_[0:1] == "["):
								realm_ = line_[1:-1].lower()
							
							elif (line_[0:1] == "#"):
								pass # ignore - comment
						
							else:
								info_ = line_.split(",")
								addressinfo_ = DAOObject({})
								
								setattrs(addressinfo_,
										 ipaddress = info_[0],
										 description = info_[1],
										 countrycode = info_[2]
										 )
										 
								addresses_[addressinfo_.ipaddress] = addressinfo_
								
					except Exception as inst:
						self.logException(inst)


	def check(self, address=None, realm=None):
		
		seenkeys_ = list(self.seen_.keys())
		now_ = self.epoch

		# have we serviced this request before... ?
		
		if (address in seenkeys_):
			addressinfo_ = self.seen_[address]
			addressinfo_.time = now_
			return addressinfo_.accept, addressinfo_.countrycode
		
		# nope - lets check it...
		
		try:
			keys_ = list(self.realms_["all"].keys())
			realmkeys_ = None
			
			if (realm in self.realms_.keys()):
				realmkeys_ = list(self.realms_[realm].keys())

			addressinfo_ = None
			
			if (address in keys_):
				addressinfo_ = self.realms_["all"][address]
			
			elif ("*" in keys_):
				addressinfo_ = self.realms_["all"]["*"]

			elif (realmkeys_ != None):
				
				addresses_ = self.realms_[realm]
				
				if (address in realmkeys_):
					addressinfo_ = addresses_[address]

				elif ("*" in realmkeys_):
					addressinfo_ = addresses_["*"]
			
			if (addressinfo_ != None):
				
				copy_ = addressinfo_.copy()
				copy_.time = now_
				copy_.accept = True
				self.seen_[address] = copy_
				
				return True, addressinfo_.countrycode
			
			else:
				self.seen_[address] = DAOObject({"ipaddress":address, "description":"blocked", "accept":False, "countrycode":"XX", "time":now_})
			
		except Exception as inst:
			self.logException(inst)

		return False, None


	def __init__(self):
	
		self.realms_ = {}
		self.seen_ = {}
		
		self.timer_ = Repeater(10.0, self.poller, self)
		self.timer_.start()
		
		self.log("Created instance of ipblock manager")
		
		self.load()



