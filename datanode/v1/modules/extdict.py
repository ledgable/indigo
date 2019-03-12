
import re
import json
import copy
import io
import base64
import inspect
import calendar, datetime

from decimal import Decimal

# this allows us to treat a dictionary like an class with properties

class extlist(list):

	
	def copy(self):
		
		return self.__class__(copy.deepcopy(list(self)))

	
	def contains(self, value, key="uid"):
		
		if (value != None) and (key != None):
			for item_ in self:
				if (item_.__getattr__(key) == value):
					return item_
		
		return None


	def toDict(self, key="uid"):
		
		if (len(self) > 0):
			return extdict({k.__getattr__(key):k for k in self})
		
		return extdict({})

			
	def __init__(self, rows=None):
				
		if (rows != None):
			
			for row_ in rows:
				
				try:
					newitem_ = None
					
					if (isinstance(row_, list)):
						newitem_ = extlist(row_)
					
					elif (isinstance(row_, dict)):
						newitem_ = extdict(row_)
					
					else:
						newitem_ = row_

					if (newitem_ != None):
						self.append(newitem_)

				except Exception as inst:
					pass

					
	@classmethod
	def fromJson(cls, jsondata=None):
		
		try:
			rowdata_ = json.loads(jsondata)
			return cls(rowdata_)
		
		except Exception as inst:
			pass
		
		return None

		
	@property
	def all(self):
		
		out_ = []
		
		for obj_ in self:
		
			value_ = obj_
		
			if isinstance(obj_, Decimal):
				value_ = float(obj_)
		
			elif isinstance(obj_, datetime.datetime):
				if obj_.utcoffset() is not None:
					obj_ = obj_ - obj_.utcoffset()
				value_ = int(calendar.timegm(obj_.timetuple()) * 1000 + obj_.microsecond / 1000)
			
			elif issubclass(obj_.__class__, extdict):
				value_ = obj_.dict()
			
			elif issubclass(obj_.__class__, extlist):
				value_ = obj_.all

			out_.append(value_)
		
		return out_

	
	def toJson(self):
		
		from modules.customencoder import CustomEncoder
		return json.dumps(self, cls=CustomEncoder, sort_keys=True)



class extdict(dict):
	
	# if you have declarations in subclasses of properties, youll need to override this or you will
	# see the values appear in the dictionary
	
	def __init__(self, row=None):

		if (row != None):
			for k,v in row.items():
				self.__setattr__(k, v)

	def dict(self):
		
		dictout_ = {}
		keys_ = self.keys()
		
		for key_ in keys_:
			
			obj_ = self[key_]
			value_ = self[key_]
			
			if isinstance(obj_, Decimal):
				value_ = float(obj_) # encode decimals for 8 decimal places
		
			elif isinstance(obj_, datetime.datetime):
				
				if obj_.utcoffset() is not None:
					obj_ = obj_ - obj_.utcoffset()
				
				value_ = int(calendar.timegm(obj_.timetuple()) * 1000 + obj_.microsecond / 1000)
			
			elif issubclass(obj_.__class__, extdict):
				value_ = obj_.dict()
			
			elif issubclass(obj_.__class__, extlist):
				value_ = obj_.all
						
			dictout_[key_] = value_
		
		return dictout_
	
	@property
	def reservedkeys(self):
		return []

	
	def toJson(self):
		from modules.customencoder import CustomEncoder
		
		return json.dumps(self, cls=CustomEncoder, sort_keys=True)

	
	@classmethod
	def fromJson(cls, jsondata=None):
		
		try:
			rowdata_ = json.loads(jsondata)
			return cls(rowdata_)
		
		except Exception as inst:
			pass
		
		return None

	
	@classmethod
	def loadJson(cls, filename=None):
		
		try:
			jsondata_ = open(filename).read()
			rowdata_ = json.loads(jsondata_)
			return cls(rowdata_)
		
		except Exception as inst:
			pass
		
		return None

	
	def __getitem__(self, item):
		
		if (item != None) and (item != ""):
			
			if (isinstance(item, str)):
				
				parts_ = item.split("\\")
				
				if (len(parts_) > 0):
					
					node_ = self.__getattr__(parts_[0])
					
					if (issubclass(node_.__class__, extdict)):
						
						if (len(parts_) > 1):
							remaining_ = ("\\").join(parts_[1:])
							return node_.__getitem__(remaining_)
						
						else:
							return node_
				
					else:
						return node_
	
		return self

	
	def remove(self, name):
	
		if (isinstance(name, str)):
			name = str(name).replace("-", "").lower()
		
			if (name in self.keys()):
				del self[name]
			
		else:
			for key_ in name:
				key_ = str(key_).replace("-", "").lower()
					
				if (key_ in self.keys()):
					del self[key_]

						
	def __sanitize(self, value):

		if (value != None):
			if (isinstance(value, str)):
				if ("%" in value):
					value = value.replace('%', '&#x25;')
	
		return value
	
	
	def __setattr__(self, name, value):
		
		name = str(name).replace("-", "").lower()
		
		try:
			
			if (name in self.reservedkeys):
				super(extdict, self).__setattr__(name, value)
			
			elif (isinstance(value, dict)):
				self[name] = extdict(value)

			elif (isinstance(value, list)):
				self[name] = extlist(value)

			else:
				self[name] = self.__sanitize(value)

		except Exception as inst:
			pass

		return value

			
	def copy(self):

		return self.__class__(copy.deepcopy(dict(self)))

	
	def default(self, name, defaultVal=None):
		
		name = str(name).replace("-", "").lower()
		value_ = self.get(name, defaultVal)

		if (value_ != None) and (value_ == ""):
			return defaultVal
		
		return value_
	
	def __getattr__(self, name):
		
		name = str(name).replace("-", "").lower()
		
		return self.get(name, None)



if __name__ == '__main__':
	
	# some test cases...
	
	print("Running some tests")
	
	jsondata_ = '{"one":"two", "two":"three"}'
	jsondata2_ = '{"ten":"two", "twenty":"three"}'

	dict_ = extdict.fromJson(jsondata_)
	
	dict_.test = extdict.fromJson(jsondata2_)
	dict_.live = dict({"sam":"programmer"})
	dict_.four = "five"
	
	print(dict_.test_)
	print(dict_.keys())
	print(dict_.two)
	print(dict_.four)
	
	dict_.test_ = "awesome"

	print(dict_.keys())
	print(dict_.test_)
	print(dict_)

	print(dict_.default("xx", "yy"))
	
	# testing xpath
	
	q_ = "test\\ten"
	print(q_)
	print(dict_[q_])
	print(dict_["live\\sam"])
