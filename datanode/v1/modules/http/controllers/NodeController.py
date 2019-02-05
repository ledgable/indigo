
from modules.http.controllers.Controller import *
from modules.chain import *
from modules.applicationmanager import *

# Common functionality to enable access to chains etc

class NodeController(Controller):
	
	
	def __init__(self, handler, session, query=None, isajax=False):
		Controller.__init__(self, handler, session, query, isajax)

	
	def chainById(self, chainid):
		
		chainid_ = chainid.lower()
		application_ = ApplicationManager(self).get("datanode")
		
		if (application_ != None):
			return application_.chainById(chainid_)
		
		return None

	
	def chains(self):
		
		application_ = ApplicationManager(self).get("datanode")
		
		if (application_ != None):
			configctrl_ = application_.configctrl
			
			if (configctrl_ != None):
				return configctrl_.chains
		
		return None

	
	def configForChain(self, chainid):
		
		chainid_ = chainid.lower()
		application_ = ApplicationManager(self).get("datanode")
		
		if (application_ != None):
			configctrl_ = application_.configctrl
			
			if (configctrl_ != None):
				return configctrl_.configForChain(chainid_)

		return None


	def hashesForChain(self, chainid):

		chainctrl_ = self.chainById(chainid)
		hashes_ = []
	
		if (chainctrl_ != None):
			chain_ = chainctrl_.chain
			if (chain_ != None):
				hashes_ = chain_.hashes()

		return hashes_


	def writeTransactionsToChain(self, chainid, transactions):
	
		chainctrl_ = self.chainById(chainid)
		shadowhash_ = None
		discarded_ = []
		deferred_ = False
		
		if (chainctrl_ != None) and (transactions != None):
			deviceid_ = chainctrl_.deviceid
			shadowhash_, discarded_, deferred_ = chainctrl_.writeTransactions(transactions)

		return shadowhash_, discarded_, deferred_


	def lastTransactions(self, chainid, count=10, hash=BASE_HASH):
		
		chainctrl_ = self.chainById(chainid)
		transactions_ = []
		
		if (chainctrl_ != None):
			chain_ = chainctrl_.chain
			
			if (chain_ != None):
				transactions_ = chain_.getLastTransactions(count, hash)

		return transactions_

	
	def transactionsInBlock(self, chainid, hash=BASE_HASH):

		chainctrl_ = self.chainById(chainid)
		transactions_ = []
	
		if (chainctrl_ != None):
			chain_ = chainctrl_.chain
			
			if (chain_ != None):
				transactions_ = chain_.readTransactionsFromChain(hash)
				
		return transactions_


	def transactionsWithKeyValue(self, chainid, classid=None, key=None, value=None, equality="==", hash=BASE_HASH):
		
		chainctrl_ = self.chainById(chainid)
		transactions_ = []
		
		if (chainctrl_ != None):
			chain_ = chainctrl_.chain
			
			if (chain_ != None):
				transactions_ = chain_.getTransactionsWithKeyValue(classid, key, value, equality, hash)

		return transactions_


	def transactionByIds(self, chainid, ids=[], hash=BASE_HASH):
	
		chainctrl_ = self.chainById(chainid)
		transactions_ = []
	
		if (chainctrl_ != None):
			chain_ = chainctrl_.chain
			
			if (chain_ != None):
				transactions_ = chain_.getTransactionsByIds(ids, 0, hash)

		return transactions_

