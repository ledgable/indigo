
import re
import threading
import json
import os
import gc
import os.path
import html
import hashlib
import operator
import uuid
import email
import copy
import io
import random
import base64
import requests
import pytz
import urllib3
import certifi
import inspect

import string, cgi, time
import sys, getopt, imp, traceback
import calendar, datetime, time

from collections import OrderedDict

from urllib.parse import parse_qs
from urllib.parse import urlparse
from urllib.parse import unquote_plus

from os import curdir, sep, path
from threading import Timer
from threading import Thread
from time import sleep

from io import StringIO
from decimal import Decimal

from config import *

from .singleton import *
from .notificationcenter import *

# generic helper component

def endpoint(*decorators):
	
	def register_wrapper(func):
		
		func._decorators=decorators
		return func
	
	return register_wrapper


# used to set properties en mass

def setattrs(_self, **kwargs):
	
	for k,v in kwargs.items():
		if (k != None) and (k != ""):
			setattr(_self, k, v)


# we capture stdin and stdout for rendering purposes so that things go to the right director etc

class RawVars(object, metaclass=Singleton):

	stdout_ = sys.stdout
	stdin_ = sys.stdin
	serviceid_ = None
	lasttext_ = ""
	debug_ = False
	timer_ = None

	
	def poller(self, args):
	
		gc.collect()
	
	
	def writeOut(self, str):
		
		if (str[-1:1] != "\n"):
			str += "\n"

		self.lasttext_ = str
		self.stdout.write(str)


	@property
	def debug(self):
		return self.debug_
	
	
	@property
	def serviceid(self):
		return self.serviceid_
	
	
	@property
	def stdout(self):
		return self.stdout_


	@property
	def stdin(self):
		return self.stdin_


	def getHwAddr(self, interested=["en0", "eth0", "en1"]):
		
		import netifaces
		
		mac_ = None
		interfaces_ = netifaces.interfaces()
		
		for interface_ in interested:
			
			if (interface_ in interfaces_):
				info_ = netifaces.ifaddresses(interface_)
				
				if (netifaces.AF_LINK in info_.keys()):
					addressinfo_ = info_[netifaces.AF_LINK]
					if (len(addressinfo_) > 0):
						mac_ = (addressinfo_[0])["addr"]
						break
	
		if (mac_ != None):
			mac_ = mac_.replace(":", "")

		return mac_
	
	
	def __init__(self):
		
		gc.disable()
		
		self.stdout_ = sys.stdout
		self.stdin_ = sys.stdin
		self.serviceid_ = self.getHwAddr()
		self.timer_ = Repeater(10.0, self.poller, self)
		self.timer_.start()


# some common functionality used by alot of code - we place it here to ensure we dont replicate code etc


rawVars_ = RawVars()
notificationCenter_ = NotificationCenter()


class BaseClass(object):
	
	def __setattr__(self, name, value):
		
		super(BaseClass, self).__setattr__(name, value)


	@property
	def stdout(self):
		
		return RawVars().stdout_


	@property
	def stdin(self):
		
		return RawVars().stdin_


	@property
	def epoch(self):
		
		return int(time.time())


	@property
	def uniqueId(self):
		
		return uuid.uuid4().hex


	@classmethod
	def hash(cls, stringin):
		
		if (stringin == None):
			return None
		
		kpt1_ = hashlib.md5()
		kpt1_.update(stringin.encode(UTF8))
		return kpt1_.hexdigest()

	# string.ascii_uppercase + string.digits
	
	def randomCode(self, size=4, chars=string.digits):
		
		return ''.join(random.choice(chars) for _ in range(size))


	def md5(self, stringin=None):
		
		return BaseClass.hash(stringin)

	
	@property
	def now(self, timezone="CET"):
		
		now = datetime.datetime.now()
		local = pytz.timezone(timezone)
		local_dt = local.localize(now, is_dst=True)
		utc_dt = local_dt.astimezone(pytz.utc)
		
		return utc_dt.strftime("%Y-%m-%d %H:%M:%S")


	def out(self, message="", errorLevel="info"):
		
		self.stdout.write("  %s\n" % (message))


	def log(self, message="", errorLevel="info"):
	
		if (RawVars().debug):
			lineno_ = inspect.currentframe().f_back.f_lineno
			RawVars().writeOut("[ \033[37m%-19s \033[36m| %-12s | %34s \033[0m] %s" % (self.now, errorLevel, (self.__class__.__name__ + ":" + str(lineno_)), message))


	def logError(self, message="", inst=None):
		
		if (RawVars().debug):
			RawVars().writeOut("[ \033[37m%-19s \033[36m| %-12s | %34s \033[0m] \033[31m%s\033[0m" % (self.now, "ERROR", self.__class__.__name__, message))
			if inst:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				trace_ = NEW_LINE.join(traceback.format_tb(exc_tb, limit=None))
				RawVars().writeOut(trace_)
				RawVars().writeOut(str(inst) + "\n")


	def logException(self, inst):
		
		if (RawVars().debug):
			self.logError("An exception occurred", inst)

