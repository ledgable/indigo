
from config import *
from dataobjects import *

from .baseclass import *
from .switch import *

DEFAULT_KEYS = ["$time", "$id"]
MAX_TRANSACTIONS_BEFORE_FLUSH = 1024
BASE_HASH = "00000000000"

CHAIN_INITIALIZING = 0
CHAIN_READY = 1


	# Terminology

	# Block			- 1024 transactions

	# Hash 			- The start of a chain - The first hash is 00000000000 which signifies the beginning of a chain

	# ShadowHash 	- As a transaction is written, the MD5 of the content (a 34 hex string) is appended to the previous transactions 'md5' in
	#				  the current block to create a sequence which then is MD5'd - the result of this is used to coordinate the nodes to ensure
	#				  data-corrpution cannot take place

	# Chain			- A sequence of blocks in a distinct order - The arrival at the end is only possible via the in-process traversing of
	#				  each block and the formulated mathematical pointer created as a result of each transaction


def shadowHash(transactions=[], basehash=BASE_HASH):
	
	if (len(transactions) == 0):
		return basehash

	transIds_ = list(o.md5hash() for o in transactions)

	# join the transactionids all in a single string... (preappend the initial hash)
	fullsequence_ = basehash + ("".join(transIds_))
	
	# hash the value
	hashval_ = hashlib.md5()
	hashval_.update(fullsequence_.encode(UTF8))
	
	return hashval_.hexdigest()


class ChainReader(BaseClass):

	uid_ = None
	buffer_ = None
	directory_ = None
	transid_ = 0
	hash_ = None
	state_ = None
	transactions_ = None

	def __init__(self, directory=None, chainid=None):
		
		self.transactions_ = []
		self.buffer_ = []
		self.uid_ = chainid
		self.transid_ = 0
		self.directory_ = directory
		self.hash_ = BASE_HASH
		self.state_ = CHAIN_INITIALIZING
		
		self.flusher_ = Repeater(10.0, self.flush, self)
		self.flusher_.start()

		NotificationCenter().postNotification(NOTIFY_CHAIN_INITIALIZED, self, None)

		self.__preload()
		self.__startup()


	@property
	def transId(self):
		
		return self.transid_


	@property
	def hash(self):
		
		return self.hash_


	@property
	def shadowHash(self):
		
		return shadowHash(self.transactions_, self.hash_)


	@property
	def uid(self):
		
		return self.uid_
	
	
	@property
	def directory(self):
		
		return self.directory_
	
	
	@property
	def transactions(self):
		
		return self.transactions_


	def hashFilename(self, hash):
		
		return ("%s.block" % (hash))


	def getFullPathForBlock(self, hash):
		
		filename_ = self.hashFilename(hash)
		
		folder_ = hash[:3] # first 3 chars of hash
		directoryfull_ = ("%s/%s" % (self.directory_, folder_))
		
		try:
			if (not os.path.exists(directoryfull_)):
				os.makedirs(directoryfull_)
		except Exception as inst:
			pass
		return ("%s/%s" % (directoryfull_, filename_))


	def updateTransIndex(self, newIndex):
		
		self.transid_ = newIndex

	
	@property
	def dirSize(self):
		
		totalsize = 0
		
		for dirpath, dirnames, filenames in os.walk(self.directory_):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				totalsize += os.path.getsize(fp)
		
		return totalsize

	
	# goes through the list and returns an array of hashes for the current ledger..
	
	def hashes(self):
		
		hash_ = BASE_HASH
		hashesout_ = [hash_]
		
		while (True):
			
			# we would get the transactions from another node (at the beginning)
			transactions_ = self.readTransactionsFromChain(hash_)
			
			if (len(transactions_) == 0) and (hash_ == BASE_HASH):
				# we potentially have a new ledger - in which case we need to go and fetch the data
				self.log("No ledger block found - we need to take action")
			
			if (len(transactions_) == 0):
				
				break
			
			elif (len(transactions_) < MAX_TRANSACTIONS_BEFORE_FLUSH):
				
				# we are at the last block in the chain
				break
			
			else:
				
				# calculate next hash to load ...
				hash_ = shadowHash(transactions_, hash_)
				hashesout_.append(hash_)
	
		return hashesout_
		
	# delete a complete chain
	
	def delete(self, confirm=False):
		
		if not confirm:
			return
		
		hashes_ = self.hashes()
		
		try:
			for hash_ in hashes_:
				url_ = self.getFullPathForBlock(hash_)
				if os.path.exists(url_):
					os.remove(url_)
	
		except Exception as inst:
			self.logException(inst)

		# now clear and reset everything..

		self.transid_ = 0
		self.hash_ = BASE_HASH
		self.state_ = CHAIN_READY
		self.transactions_ = []
	
	# deserialize a transaction into data space...
	
	def processTransaction(self, dataIn=None):

		transaction_ = None

		if (dataIn != None) and (dataIn != ""):

			try:
				transaction_ = ChainEntry.deserialize(dataIn)

			except Exception as inst:
				self.logException(inst)

		return transaction_
	
	# write transactions to disk (that arent committed
	
	def flushToDisk(self, transactions):
	
		url_ = self.getFullPathForBlock(self.hash_)
	
		with open(url_, 'a', encoding=UTF8) as fileWrite:
		
			for entry_ in transactions:
			
				remaining_ = entry_.serialize()
				index_ = 0
				
				while len(remaining_) > 0:
					
					part_ = None
					
					if len(remaining_) > MAX_LINE_LENGTH:
						part_ = remaining_[:MAX_LINE_LENGTH]
						remaining_ = remaining_[MAX_LINE_LENGTH:]
					else:
						part_ = remaining_
						remaining_ = ""
					
					if index_ == 0:
						fileWrite.write(("%s\n" % part_))
					else:
						fileWrite.write(("%s%s\n" % (TAB_CHAR, part_)))
					
					index_ += 1
			
	# read transactions from a block in the chain

	def readTransactionsFromChain(self, hash):
		
		transactionLoaded_ = []
		
		try:
			url_ = self.getFullPathForBlock(hash)
			
			if os.path.exists(url_):
				
				with open(url_, 'r', encoding=UTF8) as fileRead:
					
					line = ""
					rawtransaction_ = ""
					
					for line in fileRead:
						
						if (line != ""):
							
							if (rawtransaction_ == ""):
								rawtransaction_ = line
						
							else:
								if (line[:1] == TAB_CHAR):
									rawtransaction_ = rawtransaction_[:-1] + line[1:]
								
								else:
									transaction_ = self.processTransaction(rawtransaction_)
									if transaction_ != None:
										transactionLoaded_.append(transaction_)
									rawtransaction_ = line
	
					if (rawtransaction_ != ""):
						transaction_ = self.processTransaction(rawtransaction_)
						if transaction_ != None:
							transactionLoaded_.append(transaction_)
	
			else:
				self.log("Cannot find file %s" % (url_))

		except Exception as inst:
			self.logException(inst)
		
		return transactionLoaded_

	# begin initialization of the chain structure etc
	
	def __startup(self):
		
		self.reload()
	
	def __preload(self):
	
		pass

	def reload(self):
	
		self.hash_ = BASE_HASH
		self.state_ = CHAIN_INITIALIZING
		
		NotificationCenter().postNotification(NOTIFY_CHAIN_RESET, self, None)
		
		self.transactions_ = []
		self.updateTransIndex(0)
		
		while (True):
			
			# we would get the transactions from another node (at the beginning)
			transactions_ = self.readTransactionsFromChain(self.hash)
			
			if (len(transactions_) == 0):
				if (self.hash == BASE_HASH):
					self.log("No ledger block found for hash '%s'" % self.hash_)
				self.transactions_ = []
				break
			
			elif (len(transactions_) < MAX_TRANSACTIONS_BEFORE_FLUSH):
				self.transactions_ = transactions_
				self.updateTransIndex((transactions_[-1]["$id"]))
				NotificationCenter().postNotification(NOTIFY_CHAIN_TRANSACTIONS, self, transactions_)
				break
		
			else:
				self.hash_ = shadowHash(transactions_, self.hash_)
				self.log("New hash = %s" % self.hash_)
				self.transactions_ = []
				self.updateTransIndex((transactions_[-1]["$id"]))
				NotificationCenter().postNotification(NOTIFY_CHAIN_TRANSACTIONS, self, transactions_)

		self.state_ = CHAIN_READY
		
		NotificationCenter().postNotification(NOTIFY_CHAIN_LOADED, self, None)
		
		self.log("Transindex = %d" % (self.transid_))
		self.log("Chain is fully loaded and initialized")
	
	# write transactions to disk..
	
	def flush(self, args):
	
		if (len(self.buffer_) > 0):
			
			transactions_ = self.buffer_			
			self.buffer_ = []
			transactionstowrite_ = []
			
			for transaction_ in transactions_:
				
				if (len(self.transactions_) == MAX_TRANSACTIONS_BEFORE_FLUSH):
					
					if (len(transactionstowrite_) > 0):
						self.flushToDisk(transactionstowrite_)
						transactionstowrite_ = []
						NotificationCenter().postNotification(NOTIFY_CHAIN_TRANSACTIONS, self, transactionstowrite_)

					# we need to calculate the next hash !!
					self.hash_ = shadowHash(self.transactions_, self.hash_)

					# start a new block
					transactionstowrite_ = []
					self.transactions_ = []
						
				transactionstowrite_.append(transaction_)
				self.transactions_.append(transaction_)
			
			if (len(transactionstowrite_) > 0):
				self.flushToDisk(transactionstowrite_)
				
			# add transaction to the account history (for caching !!)
			NotificationCenter().postNotification(NOTIFY_CHAIN_TRANSACTIONS, self, transactionstowrite_)

	
	def writeTransactionsToChain(self, transactionsToWrite=None):
	
		if (self.state_ == CHAIN_INITIALIZING):
			return None
	
		if (transactionsToWrite == None) or (len(transactionsToWrite) == 0):
			return None
		
		flush_ = []
		now_ = self.epoch
		
		for transaction_ in transactionsToWrite:
			
			nextTransIndex_ = self.transId + 1
			oktowrite_ = True
			
			if (transaction_["$id"] != None):
				if (transaction_["$id"] == nextTransIndex_):
					pass # all ok - seems like the transaction ids match!
				
				else:
					# we have a chain issue - either someone is messing around (id is used by someone / something else)
					# or we have a communication from a node which doesnt quite align..
					oktowrite_ = False
		
			else:
				transaction_["$id"] = nextTransIndex_

			if (oktowrite_):
							
				# if there is no epoch in the record, add one
				
				if (transaction_["$time"] == None): # we dont change the epoch if it is already there..
					transaction_["$time"] = now_

				self.updateTransIndex(nextTransIndex_)
				self.buffer_.append(transaction_)

			
		return self.shadowHash
	
	# read contents of chain using a function to interate over the contents
	
	def readChain(self, startHash, functionToProcess=None, filter=None, since=0):
		
		if (functionToProcess == None):
			return [] # return empty set
		
		hash_ = startHash
		transactionsOut_ = []
		
		while (True):
			
			# we would get the transactions from another node (at the beginning)
			transactions_ = self.readTransactionsFromChain(hash_)
			stop_ = False
			
			if (len(transactions_) == 0):
				if (hash_ == BASE_HASH):
					self.log("No ledger found - we need to take action")
				break
			
			elif (len(transactions_) < MAX_TRANSACTIONS_BEFORE_FLUSH):
				
				filtered_, stop_ = functionToProcess(transactions_, filter, since)
				
				if (len(filtered_) > 0):
					transactionsOut_.extend(filtered_)
				
				# we are at the last block in the chain
				break
		
			else:
				
				filtered_, stop_ = functionToProcess(transactions_, filter, since)
				
				if (len(filtered_) > 0):
					transactionsOut_.extend(filtered_)

				hash_ = shadowHash(transactions_, hash_)
			
			if (len(transactionsOut_) > MAX_TRANSACTIONS_BEFORE_FLUSH):
				stop_ = True

			if stop_:
				break;
		
		return transactionsOut_


class Chain(ChainReader):
	
	controller_ = None
	
	
	def filterTransactionsForIds(self, transactionsIn=None, filter=None, since=0):
		
		out_ = []
		
		if (transactionsIn != None) and (len(transactionsIn) > 0):
			
			for transaction_ in transactionsIn:
				if (filter != None):
					if (transaction_["$id"] in filter["ids"]):
						out_.append(transaction_)
				else:
					out_.append(transaction_)
		
		return out_, False

		
	def filterTransactionsSince(self, transactionsIn=None, filter=None, since=0):
		
		out_ = []
		
		if (transactionsIn != None) and (len(transactionsIn) > 0):
			
			firstitem_ = transactionsIn[0]
			
			if (firstitem_["$time"] > since):
				out_.extend(transactionsIn)
			
			else:
				counter_ = 0
				for transaction_ in transactionsIn:
					if (transaction_["$time"] < since):
						counter_ += 1
					else:
						out_.extend(transactionsIn[counter_:])
						break
		
		return out_, False


	def filterTransactionsForIdsFrom(self, transactionsIn=None, filter=None, since=0):
	
		out_ = []
		id_ = 0
		
		if (filter != None):
			id_ = filter["id"]

		if (transactionsIn != None) and (len(transactionsIn) > 0):
			
			firstitem_ = transactionsIn[0]

			if (firstitem_["$id"] > id_):
				out_.extend(transactionsIn)
			
			elif ((firstitem_["$id"] + MAX_TRANSACTIONS_BEFORE_FLUSH) < id_):
				pass
					
			else:
				for transaction_ in transactionsIn:
					if (transaction_["$id"] > id_):
						out_.append(transaction_)
	
		return out_, False

		
	def filterTransactionsForKeyValue(self, transactionsIn=None, filter=None, since=0):
		
		out_ = []
		key_ = None
		classid_ = None
		value_ = None
		equality_ = None
		comparisonfn_ = None
		
		if (filter != None):
			key_ = filter["key"]
			classid_ = filter["classid"]
			value_ = filter["value"]
			equality_ = filter["equality"]
			comparisonfn_ = filter["comparisonfn"]

		if (comparisonfn_) and (transactionsIn != None) and (len(transactionsIn) > 0):
			
			# if we have a comparison function, execute it over the set

			for transaction_ in transactionsIn:
				if (transaction_["$class"] == classid_):
					if comparisonfn_(key_, value_, transaction_):
						out_.append(transaction_)

		return out_, False


	def getTransactionsByIds(self, transids=[], since=0, base=BASE_HASH):
		
		return self.readChain(base, self.filterTransactionsForIds, {"ids":transids}, since)

	
	def getTransactionsWithKeyValue(self, classid=None, key=None, value=None, equality="==", base=BASE_HASH):
		
		# we need to clean up the value...
		
		structures_ = self.controller_.config.structure
		
		types_ = list(structures_.keys())
		
		if (classid != None) and (classid in types_):
		
			structure_ = structures_[classid].toDict("field_name")
			keys_ = list(structure_.keys())
			keys_.extend(DEFAULT_KEYS)
			
			if (key in keys_):
				
				fieldinfo_ = structure_[key]
				datatype_ = fieldinfo_["datatype"]
				issearchable_ = (fieldinfo_["is_key"] == 1)
				
				if (issearchable_):
				
					normalizedvalue_ = value
					
					for case in switch(datatype_):
						
						if case("string"):
							normalizedvalue_ = str(value)
							break
					
						if case("integer") or case("long"):
							normalizedvalue_ = int(value)
							break
					
						if case("double") or case("float"):
							normalizedvalue_ = float(value)
							break
				
						if case("bit"):
							normalizedvalue_ = int(value)
							break
				
					if (normalizedvalue_ != None):

						fnToExecute_ = None
						
						# create a function to perform comparison over a transaction
					
						for case in switch(equality):
						
							if case("=="):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] == value_)
								fnToExecute_ = fnComparison
								break

							if case("!="):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] != value_)
								fnToExecute_ = fnComparison
								break

							if case(">"):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] > value_)
								fnToExecute_ = fnComparison
								break

							if case(">="):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] >= value_)
								fnToExecute_ = fnComparison
								break

							if case("<"):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] < value_)
								fnToExecute_ = fnComparison
								break

							if case("<="):
								def fnComparison(key_, value_, transaction_):
									return (transaction_[key_] <= value_)
								fnToExecute_ = fnComparison
								break

						return self.readChain(base, self.filterTransactionsForKeyValue, {"key":key, "value":normalizedvalue_, "classid":classid, "equality":equality, "comparisonfn":fnToExecute_}, 0)
				
				else:
					self.log("Field %s is not searchable" % (key))
					
		return []

	
	def getLastTransactions(self, count=0, base=BASE_HASH):
	
		currentindex_ = self.transId
		
		since_ = currentindex_ - count
		if (since_ < 0):
			since_ = 0

		return self.getTransactionsFrom(since_, base)

	
	def getTransactionsFrom(self, transid=0, base=BASE_HASH):
	
		return self.readChain(base, self.filterTransactionsForIdsFrom, {"id":transid}, 0)

	
	def getTransactionsSince(self, since=0, base=BASE_HASH):
		
		return self.readChain(base, self.filterTransactionsSince, {}, since)


	def writeTransactionsToChain(self, transactionsToWrite=None):
	
		hashout_ = ChainReader.writeTransactionsToChain(self, transactionsToWrite)
	
		if (self.controller_ != None):
			
			# we do a non-blocking call to inform the replication partners..
			
			idx_ = self.transId
			
			thread_ = threading.Thread(target=self.controller_.notifyReplPartners, args=(hashout_, idx_))
			thread_.daemon = True
			thread_.start()
		
		return hashout_


	def __init__(self, directory=None, chainid=None, controller=None):
		
		ChainReader.__init__(self, directory, chainid)
		
		self.controller_ = controller

		self.log("Shadowhash for chain '%s' = '%s'" % (chainid, self.shadowHash))
	
	
	@property
	def controller(self):
		return self.controller_



