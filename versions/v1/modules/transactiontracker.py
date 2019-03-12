
from .baseclass import *
from .singleton import *
from .daoobject import *
from .repeater import *

class TransactionTracker(BaseClass, metaclass=Singleton):
	
	timer_ = None
	transactions_ = None
	
	def newTransaction(self, functionin=None, timeout=30):
		
		if (functionin == None):
			return None
		
		transaction_ = DAOObject({})
		transaction_.uid = self.uniqueId
		transaction_.function = functionin
		transaction_.expires = self.epoch + timeout
		
		self.transactions_[transaction_.uid] = transaction_
		
		return transaction_.uid
	
	def functionForId(self, uid):
		
		transids_ = list(self.transactions_.keys())
		
		if (uid in transids_):
			transactioninfo_ = self.transactions_[uid]
			del self.transactions_[uid]
			
			return transactioninfo_.function
		
		return None
	
	def poller(self, args):
		
		transids_ = list(self.transactions_.keys())
		
		if (len(transids_) > 0):
			now_ = self.epoch
			
			for transid_ in transids_:
				transaction_ = self.transactions_[transid_]
				
				if (now_ > transaction_.expires):
					self.log("Expired transaction %s" % (transid_))
					del self.transactions_[transid_]

	def __init__(self):
		
		self.log("Creating transaction tracker singleton")
	
		self.transactions_ = {}
		self.timer_ = Repeater(5.0, self.poller, self)
		self.timer_.start()
