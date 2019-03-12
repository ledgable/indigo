
import json

import sys, getopt, imp, traceback
import calendar, datetime

from decimal import Decimal

class CustomEncoder(json.JSONEncoder):
	
	def default(self, obj):
		
		from modules.daoobject import DAOObject, DAOCollection
		
		try:
			
			if isinstance(obj, Decimal):
				return float(obj)
			
			return json.JSONEncoder.default(self, obj)
		
		except Exception as inst:
			pass
		
		return None
