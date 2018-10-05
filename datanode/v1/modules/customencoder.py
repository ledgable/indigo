
import json

import sys, getopt, imp, traceback
import calendar, datetime

from decimal import Decimal

class CustomEncoder(json.JSONEncoder):
	
	def default(self, obj):
		
		from modules.daoobject import DAOObject, DAOCollection

		out_ = None
		
		try:
			
			if isinstance(obj, Decimal):
				out_ = ("%.8f" % obj) # encode decimals for 8 decimal places
			
			elif isinstance(obj, datetime.datetime):
				if obj.utcoffset() is not None:
					obj = obj - obj.utcoffset()
				millis = int(calendar.timegm(obj.timetuple()) * 1000 + obj.microsecond / 1000)
				out_ = millis
			
			elif issubclass(obj.__class__, DAOObject):
				out_ = obj.__dict__()
			
			elif issubclass(obj.__class__, DAOCollection):
				out_ = obj.all
			
			else:
				out_ = json.JSONEncoder.default(self, obj)
	
		except Exception as inst:
			pass
		
		return out_
