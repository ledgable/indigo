
import pytz
import datetime
import time
import hashlib

from modules.daoobject import *

class Session(DAOObject):

	def __init__(self, row=None):		
		DAOObject.__init__(self, row)

	@property
	def id_session(self):
		return self.session

	@property
	def timezone(self):
		return pytz.timezone("UTC")
