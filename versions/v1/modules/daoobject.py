
from .extdict import *


	# This class transforms a json data object into a class based object (or collection) for
	# querying in a standardized manner to properties


class DAOObject(extdict):
	
	modified_ = False
	
	
	@property
	def reservedkeys(self):
		return ["modified_"]

	
	def __setattr__(self, name, value):
		
		if (name != "modified_"):
			extdict.__setattr__(self, "modified_", True)
		
		return extdict.__setattr__(self, name, value)


	def __init__(self, row=None):
		
		extdict.__init__(self, row)
		
		self.modified_ = (row != None)


class DictObject(DAOObject):
	
	
	def __init__(self, vars=None):
		
		DAOObject.__init__(self, vars)


class DAOCollection(extlist):
	
	itemClass_ = None
	
	@property
	def itemClass(self):
		
		return self.itemClass_

	
	@property
	def len(self):
		
		return len(self)

	
	@property
	def items(self):
		
		return self

	
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
		self.append(item)
	
	
	def filtered(self, key, value):
		# to be implemented...
		return None

	
	def __init__(self, rows=None, itemClass=DAOObject):
		
		self.itemClass_ = itemClass
		
		if (rows != None):
			
			if (self.itemClass_ != None):
				
				for row_ in rows:
					
					newitem_ = None
					
					if (isinstance(row_, list)) or (isinstance(row_, extlist)):
						newitem_ = DAOCollection(row_, itemClass)
					
					elif (isinstance(row_, dict)) or (isinstance(row_, extdict)):
						newitem_ = itemClass(row_)
					
					else:
						newitem_ = row_
					
					self.append(newitem_)
		
			else:
				self.extend(rows)


	def copy(self):
		
		out_ = self.__class__([], self.itemClass_)
		
		for item_ in self:
			out_.append(item_.copy())
		
		return out_
		

	def remove(self, name):
		
		if (len(self) > 0):
			for item_ in self:
				item_.remove(name)

	
	@property
	def firstitem(self):

		if (len(self) > 0):
			return self[0]
														 
		return None
														 

	@property
	def item(self, index=0):
	
		if (index < len(self)):
			value_ = json.dumps(self[index], cls=CustomEncoder, sort_keys=True)
			return value_
		
		return None

	
	@classmethod
	def fromJson(cls, jsondata=None, itemClass=DAOObject):
		
		try:
			rowdata_ = json.loads(jsondata)
			return cls(rowdata_, itemClass)
		
		except Exception as inst:
			pass
		
		return None


if __name__ == '__main__':

	testdict_ = {"one":"two", "two":"three"}

	daoobject_ = DAOObject(testdict_)

	copiedobject_ = daoobject_.copy()
	copiedobject_.three = "four"
	
	print(daoobject_)
	print(daoobject_.modified_)
	
	print(copiedobject_)
	print(copiedobject_.modified_)

	testarray_ = [{"one":"two", "two":"four"}, {"one":"two", "two":"three"}, {"one":"two", "two":"eight"}]

	daocollection_ = DAOCollection(testarray_)

	print(daocollection_)
	print(daocollection_.toDict("two"))
	print(len(daocollection_))

	copycollection_ = daocollection_.copy()
	print(copycollection_)
