
class TreeNode:
	
	@property
	def parent(self):
		return self.parent_
	
	@property
	def level(self):
		if (self.parent_ == None):
			return 0
		return (1 + self.parent_.level)
	
	@property
	def data(self):
		return self.data_
	
	@property
	def uid(self):
		return self.uid_
	
	@property
	def children(self):
		return list(self.children_.values())

	@property
	def childdata(self):
		out_ = []
		if (len(self.children_) > 0):
			for child_ in list(self.children_.values()):
				out_.append(child_.data)
		return out_
	
	@property
	def isroot(self):
		return (self.parent_ == None)
	
	def __init__(self, uid=None, data=None, parent=None):
		
		self.uid_ = uid
		self.data_ = data
		self.parent_ = parent
		self.children_ = {}
	
	def find(self, uid=None):
		
		if (uid == None):
			return None
		
		if (self.uid_ == uid):
			return self

		found_ = None

		if (len(self.children_) > 0):
			for child_ in self.children_.values():
				result_ = child_.find(uid)
				if (result_ != None):
					found_ = result_
					break

		return found_
	
	@property
	def enumerate(self):
		out_ = [self]
		if (self.parent_ != None):
			out_.extend(self.parent_.enumerate)
		return out_
			
	def toString(self, lvl=0):
		
		out_ = ""
		
		if (self.uid_ == None):
			out_ += "Root\r\n"
		
		else:
			if (self.data_ != None):
				out_ += "%s - %s%s\r\n" % (self.uid_, ("\t" * lvl), self.data_)
			
			else:
				out_ += "%s\r\n" % (self.uid_)
		
		if (len(self.children_) > 0):
			
			for child_ in list(self.children_.values()):
				out_ += child_.toString(lvl+1)
		
		return out_
	
	def append(self, listdata=None, key="uid", searchon="id_parent"):
	
		if (listdata != None):
		
			for item_ in listdata:
				
				uid_ = item_[key]
				
				if (uid_ == ""):
					uid_ = None
				
				parentid_ = item_[searchon]
				
				if (parentid_ == ""):
					parentid_ = None
				
				if (parentid_ != None):
					entrypoint_ = self.find(parentid_)
					
					if (entrypoint_ != None):
						entrypoint_.addChild(uid_, item_, entrypoint_)
					
					else:
						pass # we have an unallocated item
		
				else: # add at root as this is likely a new coin issue
					self.addChild(uid_, item_, None)

	def addChild(self, uid=None, data=None, parent=None):
		
		if (data == None) or (uid == None):
			return
		
		treenode_ = None
		
		# we keep the chain in the same class type...

		if (uid not in self.children_.keys()):
			
			treenode_ = self.__class__(uid, data, parent)
			self.children_[uid] = treenode_

