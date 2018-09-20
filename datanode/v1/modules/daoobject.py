
from .baseclass import *


	# This class transforms a json data object into a class based object (or collection) for
	# querying in a standardized manner to properties


class DAOObject(BaseClass):
	
	def reservedkeys(self):
		
		return ['row_', 'modified_']
	
	def __getitem__(self, item):
	
		if (item != None) and (item != ""):
			
			if (isinstance(item, str)):
				
				parts_ = item.split("\\")
				
				if (len(parts_) > 0):
					node_ = self.__getattr__(parts_[0])
					
					if (issubclass(node_.__class__, DAOObject)):
						remaining_ = ("\\").join(parts_[1:])
					
						if (len(remaining_) > 0):
							return node_.__getitem__(remaining_)
						else:
							return node_
								
					else:
						return node_
							
		return self
	
	def __getattr__(self, name):
		
		if (name == "row_"):
			return self.row_
		
		name = str(name).replace("-", "").lower()
		
		if (self.row_ != None):
			return self.row_.get(name, None)
		
		return None
	
	def __setattr__(self, name, value):
		
		if (name in self.reservedkeys()):
			return super(DAOObject, self).__setattr__(name, value)
		
		name = str(name).replace("-", "").lower()
		
		try:
			
			if (value == None):
				self.row_[name] = None
		
			elif (isinstance(value, list)):
				self.row_[name] = DAOCollection(value)
			
			elif (isinstance(value, dict)):
				self.row_[name] = DAOObject(value)

			elif (name[-1:] == "_"):
				super(DAOObject, self).__setattr__(name, value)

			else:
				self.row_[name] = value

		except Exception as inst:
			self.logError("Error - self = %s, name = %s, value = %s" % (self, name, value), inst)
			
		self.modified_ = True
		
		return value

	def default(self, name, defaultVal=None):
	
		name = str(name).replace("-", "").lower()
		
		return self.row_.get(name, defaultVal)
	
	def remove(self, name):
		
		if (self.row_ != None):		
			if (isinstance(name, str)):
				name = str(name).replace("-", "").lower()
				
				if (name in self.row_.keys()):
					del self.row_[name]
		
			else:
				for key_ in name:
					key_ = str(key_).replace("-", "").lower()
					
					if (key_ in self.row_.keys()):
						del self.row_[key_]

	def keys(self):
		
		if (self.row_ != None):
			return list(self.row_.keys())
		
		return []

	def __dir__(self):
		
		return list(self.row.keys())

	def copy(self):
		
		return self.__class__(copy.deepcopy(self.row_))
	
	def __init__(self, row=None):
		
		self.row_ = {}

		if (row != None) and (isinstance(row, dict)):
			
			for k,v in row.items():
				self.__setattr__(k, v)
		
			self.modified_ = True
	
		else:
			
			self.modified_ = False

	def __repr__(self):
		
		return "%s" % self.__dict__()

	def __dict__(self):
		
		return self.row_
	
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

class DictObject(DAOObject):
	
	def __init__(self, vars=None):
		
		DAOObject.__init__(self, vars)

class DAOCollection(BaseClass):
	
	items_ = None
	
	def __iter__(self):
		
		self.n_ = 0
		return self
	
	def __next__(self):
		
		if (self.items_ != None):
			
			if (self.n_ < len(self.items_)):
				result_ = self.items_[self.n_]
				self.n_ += 1
				return result_
		
		raise StopIteration
	
	def __len__(self):
		
		if (self.items_ != None):
			return len(self.items_)
		
		return 0
	
	def contains(self, value, key="uid"):
		
		if (value != None) and (key != None):
			for item_ in self:
				if (item_.__getattr__(key) == value):
					return item_

		return None

	def toDict(self, key="uid"):
		
		if (len(self) > 0):
			return {k.__getattr__(key):k for k in self}
		
		return {}
	
	@property
	def len(self):
		
		if (self.items_ != None):
			return len(self.items_)
		
		return 0
	
	@property
	def items(self):
		
		return self.items_
	
	def sortBy(name=None):
		
		if (name == None):
			return self
		
		name = str(name).replace("-", "").lower()
		rows_ = self.all
		sorteddict_ = sorted(rows_, key=lambda k: k[name])
		copy_ = DAOCollection(sorteddict_, self.itemClass_)
		
		return copy_
	
	@property
	def cachable(self):
		
		return 0
	
	def addItem(self, item):
		
		self.items_.append(item)
	
	def filtered(self, key, value):
		# to be implemented...
		return None
	
	def __getitem__(self, item):
		
		return self.items[item]
	
	def __init__(self, rows=None, itemClass=DAOObject):
		
		self.items_ = []
		self.itemClass_ = itemClass
		
		if (rows != None):
			if (self.itemClass_ != None):
				for row_ in rows:
					
					newitem_ = None
					
					if (isinstance(row_, list)):
						newitem_ = DAOCollection(row_, itemClass)
					
					elif (isinstance(row_, dict)):
						newitem_ = itemClass(row_)
					
					else:
						newitem_ = row_
					
					self.items_.append(newitem_)
		
			else:
				self.items_ = rows

	def copy(self):
		
		copy_ = DAOCollection(None, self.itemClass_)
		
		for item_ in self.items_:
			copy_.addItem(item_.copy())
		
		return copy_

	def remove(self, name):
		
		if self.items_ != None and (len(self.items_) > 0):
			for item_ in self.items_:
				item_.remove(name)

	@property
	def all(self):
		
		out_ = []
		
		if self.items_ != None and (len(self.items_) > 0):
			
			for item_ in self.items_:
				
				if (issubclass(item_.__class__, DAOObject)):
					out_.append(item_.__dict__())
				
				elif (issubclass(item_.__class__, DAOCollection)):
					out_.append(item_.all)
				
				else:
					out_.append(item_)
	
		return out_
	
	@property
	def firstitem(self):
		
		if self.items_ != None and (len(self.items_) > 0):
			return self.items_[0]
		return None
	
	@property
	def item(self, index=0):
		
		if (self.items_ != None) and (index < len(self.items_)):
			return self.items_[index]
		
		return None

	@classmethod
	def fromJson(cls, jsondata=None, itemClass=DAOObject):
		
		try:
			rowdata_ = json.loads(jsondata)
			return cls(rowdata_, itemClass)
		
		except Exception as inst:
			pass
		
		return None

	def toJson(self):
		
		from modules.customencoder import CustomEncoder

		return json.dumps(self, cls=CustomEncoder, sort_keys=True)

	def __repr__(self):
		
		return "%s" % self.all
