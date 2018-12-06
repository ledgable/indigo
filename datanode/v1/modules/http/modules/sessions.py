
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

from dataobjects import *

TIMEOUT = 10

#####################################
####
####  Runtime Session Manager
####
#####################################

class SessionMgr(BaseClass):

	secCode = None
	dbname_ = None
	sessions_ = None
	
	def invalidate(self, sessionid):
		
		sessionkeys_ = list(self.sessions_.keys())
		
		if (sessionid in sessionkeys_):
			self.log("Invalidating session %s due to change" % sessionid)
			del self.sessions_[sessionid]
		
		# reload the session info
		return self.sessionForId(sessionid)
	
	def verifySession(self, sessionid, ipaddress):
		
		if (sessionid in self.sessions_.keys()):
			sessioninfo_ = self.sessions_[sessionid]
			if (sessioninfo_.ip_address == ipaddress):
				return sessionid

		return None
	
	def poller(self, args):
		
		keys_ = list(self.sessions_.keys())
		now_ = self.epoch
		
		for key_ in keys_:
			session_ = self.sessions_[key_]
			if (session_.date_updated) < (now_ - TIMEOUT):
				self.log("Session %s invalidated" % key_)
				del self.sessions_[key_]
	
	def sessionForId(self, sessionid):

		if (sessionid == NO_TRACK):
			return self.noTrackSession
		
		# if we look at it, change the information accordingly and write back to the service..
		
		sessioninfo_ = None
		sessionkeys_ = list(self.sessions_.keys())
		
		if (sessionid in sessionkeys_):
			sessioninfo_ = self.sessions_[sessionid]
			sessioninfo_.date_updated = self.epoch
			
		else:
			pass
		
		return sessioninfo_

	def __init__(self):
		
		self.NO_TRACKING_SESSION_ = None
		self.sessions_ = {}
		
		timer = Repeater(5.0, self.poller, self)
		timer.start()
	
		self.log("Created instance of sessions manager")
	
	@property
	def sessions(self):
		return self.sessions_
	
	@property
	def noTrackSession(self):
		
		if (self.NO_TRACKING_SESSION_ == None):
			
			sessioninfo_ = Session({})
			
			setattrs(sessioninfo_,
				session = NO_TRACK,
				ip_address = "0.0.0.0",
				lang = "en",
				country_code="NL",
				device_type = "",
				user_agent = "",
				date_created = 0,
				date_updated = 0
				)

			self.NO_TRACKING_SESSION_ = sessioninfo_
	
		return self.NO_TRACKING_SESSION_

	def newSession(self, ipaddress, language="en", device_type="safari", userAgent=None, country_code="NL"):

		sessionid_ = self.uniqueId
		sessioninfo_ = Session({})
		
		setattrs(sessioninfo_,
				 session = sessionid_,
				 ip_address = ipaddress,
				 lang = language,
				 device_type = device_type,
				 user_agent = userAgent,
				 country_code = country_code,
				 date_created = self.epoch,
				 date_updated = self.epoch,
				 auth_token = self.uniqueId,
				 )

		self.sessions_[sessionid_] = sessioninfo_

		return sessioninfo_
