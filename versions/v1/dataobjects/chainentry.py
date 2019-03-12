
import hashlib

from config import *

from modules.daoobject import *

class ChainEntry(DAOObject):
	
	def serialize(self):
		return self.toJson()
	
	@classmethod
	def deserialize(cls, data=None):
		return cls.fromJson(data)
	
	def md5hash(self):
		hashval_ = hashlib.md5()
		hashval_.update(self.toJson().encode(UTF8))
		hashresult_ = hashval_.hexdigest()
		return hashresult_

