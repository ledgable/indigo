
# Copyright (C)2017 Ledgable BV

from modules.http.controllers.NodeController import *

class DataNodeController(NodeController):

	def __init__(self, handler, session, query=None, isajax=False):
		NodeController.__init__(self, handler, session, query, isajax)

	# get chains for datanode
	
	@endpoint(1, False, True, None, "get", "^/api/datanode/chains", "Get chains")
	def getChains(self, postData=None, appVars=None, chainid=None):
		
		chains_ = self.chains()
		
		return FunctionResponse(HTTP_OK, TYPE_JSON, {"chains":chains_})
	
	# retrieve the configuration for node x

	@endpoint(1, False, True, None, "get", "^/api/datanode/(?P<chainid>[0-9a-f][^-&*/\%]*)/config", "Get chain configuration info")
	def getConfigForChain(self, postData=None, appVars=None, chainid=None):

		config_ = self.configForChain(chainid)

		return FunctionResponse(HTTP_OK, TYPE_JSON, {"chainid":chainid, "config":config_})
	
	# retrieve the hashes for node x

	@endpoint(1, False, True, None, "get", "^/api/datanode/(?P<chainid>[0-9a-f][^-&*/\%]*)/hashes", "Get chain hashes")
	def getHashesForChain(self, postData=None, appVars=None, chainid=None):

		hashes_ = self.hashesForChain(chainid)

		return FunctionResponse(HTTP_OK, TYPE_JSON, {"chainid":chainid, "hashes":hashes_})

	# retrieve transactions for node x (by hash or id of transaction)

	@endpoint(1, False, True, None, "get", "^/api/datanode/(?P<chainid>[0-9a-f][^-&*/\%]*)/transactions/(?P<mode>(hash|id))/(?P<arg>[0-9a-f,][^-&*/\%]*)", "Get transactions for block in chain or by id")
	def getTransactionsForChainInBlock(self, postData=None, appVars=None, chainid=None, mode="hash", arg=None):
		
		transactions_ = []
		
		if (mode == "hash"):
			transactions_ = self.transactionsInBlock(chainid, arg)
		
		elif (mode == "id"):
			ids_ = list(map(int, arg.split(",")))
			transactions_ = self.transactionByIds(chainid, ids_)

		return FunctionResponse(HTTP_OK, TYPE_JSON, {"chainid":chainid, "transactions":transactions_})

			
	# retrieve transactions for node x where key equals value
			
	@endpoint(1, False, True, None, "get", "^/api/datanode/(?P<chainid>[0-9a-f][^-&*/\%]*)/transactions/key/(?P<key>[0-9a-z][^-&*/\%]*)/(?P<value>[0-9a-z][^-&*/\%]*)", "Get transactions for block for key with value")
	def getTransactionsForKeyAndValue(self, postData=None, appVars=None, chainid=None, key=None, value=None):
			
		transactions_ = self.transactionsWithKeyValue(chainid, key, value)
						
		return FunctionResponse(HTTP_OK, TYPE_JSON, {"chainid":chainid, "transactions":transactions_})

	
	# Write a transaction into the chain - goes via the chaincontroller
	
	@endpoint(1, False, True, None, "post", "^/api/datanode/(?P<chainid>[0-9a-f][^-&*/\%]*)", "Write a transaction")
	def writeTransactions(self, postData=None, appVars=None, chainid=None):
		
		if (postData != None):

			try:
				shadowhash_ = None
				discarded_ = None
				transactions_ = json.loads(postData.decode(UTF8))
				
				shadowhash_, discarded_, deferred_ = self.writeTransactionsToChain(chainid, transactions_)

				return FunctionResponse(HTTP_OK, TYPE_JSON, {"chainid":chainid, "hash":shadowhash_, "discarded":discarded_, "deferred":deferred_})

			except Exception as inst:
				self.logException(inst)

		return FunctionResponse(HTTP_NOT_ACCEPTABLE, TYPE_JSON, [])

