
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

class NotificationCenter(metaclass=Singleton):
	
	listeners_ = None

	
	def addObserver(self, named, fnserver=None):
	
		if (fnserver == None):
			return
	
		named_ = named.lower()
		
		if (named_ in self.listeners_.keys()):
			observers_ = self.listeners_[named_]
			observers_.append(fnserver)
			self.listeners_[named_] = observers_
		
		else:
			self.listeners_[named_] = [fnserver]


	def threadedPostNotification(self, named, caller=None, object=None):
	
		named_ = named.lower()
		
		if (named_ in self.listeners_.keys()):
			observers_ = self.listeners_[named_]
			
			for observer_ in observers_:
				if (observer_):
					observer_(caller, object)


	def postNotification(self, named, caller=None, object=None):
	
		t = threading.Thread(target=self.threadedPostNotification, args=[named, caller, object])
		t.daemon = True
		t.start()
	
	
	def __init__(self):
		
		self.listeners_ = {}
		
