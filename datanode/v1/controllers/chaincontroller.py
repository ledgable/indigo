
from modules import *

from .configcontroller import *

DEFAULT_KEYS = ["$time", "$id", "$class"]

class ChainController(BaseClass):


	timer_ = None
	manager_ = None
	
	chain_ = None
	chainid_ = None
	chainmode_ = None
	
	configupdated_ = False
	
	connections_ = None
	
	cachedir_ = None
	chaindir_ = None
	datadir_ = None

	cachedtransactions_ = None
	lock_ = None
	

	@property
	def chain(self):
		return self.chain_


	@property
	def chainid(self):
		return self.chainid_
	
	
	@property
	def deviceid(self):
		return self.manager_.appInstance.deviceid


	@property
	def config(self):
		
		if (self.chainid_ != None):
			config_ = ConfigController().configForChain(self.chainid_)
			return config_
				
		return None


	def sendMessageToPartners(self, partners=None, message=None):
	
		if (partners != None) and (len(partners) > 0) and (message != None):
			
			for partner_ in partners:
			
				keyid_ = partner_.uid				
				if (keyid_ != self.deviceid):

					connections_ = list(self.connections_.keys())
					
					self.log("Sending message to %s" % partner_)
					
					if (keyid_ not in connections_):
						
						certpartner_ = ("%s.cer" % keyid_)
						connection_ = TimedSocketConnectionOut(keyid_, partner_.ip_address, self.messageReceived, None, self.disconnectSuccess, self.failedConnect, certpartner_)
						self.connections_[keyid_] = connection_
					
					else:
						# connection already established to service
						connection_ = self.connections_[keyid_]
					
					connection_.send(message)


	def setConfigUpdated(self):
		
		self.configupdated_ = True
		self.timer_.interval = 2


	def setChainMode(self, chainmode="o"):
		
		if (chainmode != self.chainmode_):		
			self.chainmode_ = chainmode
			self.log("Changing chain mode to %s" % self.chainmode_)
			self.requestCurrentStatus()


	def failedConnect(self, socket=None):

		keys_ = list(self.connections_.keys())
		key_ = socket.key_
		
		self.log("Failed to connect received %s" % key_)

		if (key_ in keys_):
			del self.connections_[key_]
			self.log("Removing connection %s as disconnected" % key_)


	def disconnectSuccess(self, socket=None):
		
		keys_ = list(self.connections_.keys())
		key_ = socket.socketmgr_.key_
		
		self.log("Disconnect received for %s" % key_)

		if (key_ in keys_):
			del self.connections_[key_]
			self.log("Removing connection %s as disconnected" % key_)


	def isAccessAllowed(self, deviceid):
		
		if (deviceid != None):
			
			partners_ = self.config.partners.toDict()			
			source_ = partners_[deviceid]
			
			if (source_ != None):
				return source_.mode

		return ACCESS_NONE
	
	
	def findPartners(self, permissionset=[], type="node"):
		
		config_ = self.config
		possibles_ = []
		
		if (config_ != None):
			partners_ = config_.partners
			
			if (partners_ != None) and (len(partners_) > 0):
				
				for partner_ in partners_:
					if (partner_.uid != self.deviceid):
						if (partner_.type == type) or (type == "all"):
							if (partner_.mode in permissionset):
								possibles_.append(partner_.copy())
		
		return possibles_


	def writeTransactions(self, transactions=None):
		
		discarded_ = []
		shadowhash_ = None
		deferred_ = False
		
		if (transactions != None) and (len(transactions) > 0):

			if (self.chainmode_ == ACCESS_MASTER):
				
				# is this the only master ?
				
				partners_ = self.findPartners([ACCESS_MASTER])
				
				if (len(partners_) == 0):
					# ok to write - no syncing required... no other masters out there...
					pass
				
				else:
					# push transactions to cache...
					self.cachedtransactions_.extend(transactions)
					
					if (self.lock_ == None):
					
						transactionid_ = self.uniqueId
					
						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_GET_SYNC_LOCK)
						message_.writeString(transactionid_)
						message_.writeString(self.deviceid)
						message_.writeString(self.chainid_)
						
						self.sendMessageToPartners(partners_, message_)
					
						return None, [], transactions
							
					elif (self.lock_ == self.deviceid):
					
						# lock is confirmed.. write thru transactions
					
						pass
					
					else:
						return None, [], transactions
				
				if (self.chain_ != None):
				
					committed_ = []
					
					# we verify the structure of each transaction
					allrecords_ = self.config.structure
					allrecordsids_ = list(allrecords_.keys())
					fieldchecker_ = {}
					
					for recordid_ in allrecordsids_:
						# mutate the structure so that we have a dictionary with the field_name as the key
						fieldchecker_[recordid_] = allrecords_[recordid_].toDict("field_name")
					
					for transaction_ in transactions:
						typeid_ = transaction_.get("$class", None)
					
						if (typeid_ != None) and (typeid_ in allrecordsids_):
							structure_ = fieldchecker_[typeid_]
							keys_ = list(structure_.keys())
							keys_.extend(DEFAULT_KEYS)
						
							# we only copy over the data thats held in the keys
							sanitizedtransaction_ = {}

							for key_ in keys_:
								value_ = transaction_.get(key_, None)
								if (value_ is not None):
									sanitizedtransaction_[key_] = value_

							doatransaction_ = ChainEntry(sanitizedtransaction_)

							if (len(doatransaction_.keys()) > 0):
								committed_.append(doatransaction_)

							else:
								# if the record is not compliant (ie no structure matches, we discard it)
								discarded_.append(transaction_)
					
						else:
							discarded_.append(transaction_)
					
					if (len(committed_) > 0):
						shadowhash_ = self.chain_.writeTransactionsToChain(committed_)
							
					if (self.lock_ == self.deviceid):
						partners_ = self.findPartners([ACCESS_MASTER])
												
						transactionid_ = self.uniqueId
						
						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_SYNC_RELEASE)
						message_.writeString(transactionid_)
						message_.writeString(self.deviceid)
						message_.writeString(self.chainid_)
						
						self.sendMessageToPartners(partners_, message_)
						
		
			else:
				
				# unless you are the master, we do not allow you to send messages directly into the chain

				from modules.customencoder import CustomEncoder
				transactiondata_ = json.dumps(transactions, cls=CustomEncoder, sort_keys=True)

				if (transactiondata_ != None):

					partners_ = self.findPartners([ACCESS_MASTER])
					
					transactionid_ = self.uniqueId
					
					message_ = MessageWriter()
					message_.writeByte(SOCKET_MESSAGE_WRITE_TRANSACTION)
					message_.writeString(transactionid_)
					message_.writeString(self.deviceid)
					message_.writeString(self.chainid)
					message_.writeString(transactiondata_)
					
					self.sendMessageToPartners(partners_, message_)
					
					deferred_ = transactionid_

		return shadowhash_, discarded_, deferred_


	def writeTransactionsToChain(self, transactions=None, sourceDeviceId=None):
	
		discarded_ = []
		shadowhash_ = None

		if (self.chain_ != None):

			mode_ = self.isAccessAllowed(sourceDeviceId)
			
			if (mode_ in [ACCESS_WRITEONLY, ACCESS_PUBLIC, ACCESS_READWRITE, ACCESS_MASTER]):
	
				committed_ = []
				
				# we verify the structure of each transaction
				allrecords_ = self.config.structure
				allrecordsids_ = list(allrecords_.keys())
				fieldchecker_ = {}
				
				for recordid_ in allrecordsids_:
					# mutate the structure so that we have a dictionary with the field_name as the key
					fieldchecker_[recordid_] = allrecords_[recordid_].toDict("field_name")

				for transaction_ in transactions:
					typeid_ = transaction_.get("$class", None)
						
					if (typeid_ != None) and (typeid_ in allrecordsids_):
						structure_ = fieldchecker_[typeid_]
						keys_ = list(structure_.keys())
						keys_.extend(DEFAULT_KEYS)

						# we only copy over the data thats held in the keys
						sanitizedtransaction_ = {}
						
						for key_ in keys_:
							value_ = transaction_.default(key_, None)
							if (value_ is not None):
								sanitizedtransaction_[key_] = value_
					
						doatransaction_ = ChainEntry(sanitizedtransaction_)
						
						if (len(doatransaction_.keys()) > 0):
							committed_.append(doatransaction_)
						
						else:
							# if the record is not compliant (ie no structure matches, we discard it)
							discarded_.append(transaction_)
		
					else:
						discarded_.append(transaction_)

				if (len(committed_) > 0):
					shadowhash_ = self.chain_.writeTransactionsToChain(committed_)

			else:
				discarded_ = transactions
						
		return shadowhash_, discarded_


	def requestCurrentStatus(self):
	
		if (self.chainmode_ != ACCESS_NONE):
			
			possibles_ = self.findPartners([ACCESS_MASTER, ACCESS_READWRITE, ACCESS_WRITEONLY, ACCESS_PUBLIC])
			
			if (len(possibles_) > 0):
				
				self.log("Found %d replication partners" % len(possibles_))

				shadowhash_ = self.chain_.shadowHash
				transid_ = self.chain_.transId
				chainid_ = self.chainid_
				deviceid_ = self.deviceid
				
				transactionid_ = self.uniqueId
				
				message_ = MessageWriter()
				message_.writeByte(SOCKET_MESSAGE_GET_STATUS)
				message_.writeString(transactionid_)
				message_.writeString(deviceid_)
				message_.writeString(chainid_)
				
				self.sendMessageToPartners(possibles_, message_)
			
			else:
				self.log("No replication partners found")
				

	def poller(self, args):
		
		if (self.configupdated_):
			self.configupdated_ = False
			self.timer_.interval = TIME_INTERVAL_REQUEST_IDXUPDATED
			
			self.loadChain()
			self.checkReplState()

		if (self.chain_ != None):
			pass


	def createDirectories(self):
		
		success_ = True
		
		if (self.chainid_ == None):
			return False
		
		try:
			chaindir_ = self.manager_.devicedir + ("/%s" % self.chainid_)
			
			if (not os.path.exists(chaindir_)):
				self.log("Chain Directory does not exist - creating")
				os.makedirs(chaindir_)
			
			# under a node, you have the relevant storage objects
			
			self.cachedir_ = chaindir_ + "/cache"
			self.datadir_ = chaindir_ + "/data"
			
			if (not os.path.exists(self.cachedir_)):
				self.log("Cache Directory does not exist - creating")
				os.makedirs(self.cachedir_)
			
			if (not os.path.exists(self.datadir_)):
				self.log("Chain Data Directory does not exist - creating")
				os.makedirs(self.datadir_)
		
		except Exception as inst:
			self.logException(inst)
			success_ = False
				
		return success_


	def checkReplState(self):
	
		if (self.config == None):
			return
		
		partners_ = self.config.partners

		if (partners_ != None) and (len(partners_) > 0):

			for partner_ in partners_:
				if (partner_.uid == self.deviceid):
					self.setChainMode(partner_.mode)


	def loadChain(self):
		
		if (self.config == None):
			return
			
		if (self.chain_ == None):
			self.chain_ = Chain(self.datadir_, self.chainid_, self)
		
		else:
			pass


	def getBlockForChain(self, socket=None, hash=None):
	
		if (socket != None) and (hash != None):
			
			transactionid_ = self.uniqueId
			
			message_ = MessageWriter()
			message_.writeByte(SOCKET_MESSAGE_GET_BLOCK)
			message_.writeString(transactionid_)
			message_.writeString(self.deviceid)
			message_.writeString(self.chainid)
			message_.writeString(hash)
		
			socket.send(message_)


	def sendHashRequest(self, socket=None):

		if (socket != None):
			
			transactionid_ = self.uniqueId

			message_ = MessageWriter()
			message_.writeByte(SOCKET_MESSAGE_GET_HASHLIST)
			message_.writeString(transactionid_)
			message_.writeString(self.deviceid)
			message_.writeString(self.chainid)
			
			socket.send(message_)


	# be aware this is (potentially) called on a separate thread !!

	def messageReceived(self, messageId, content=None, socket=None):
	
		self.log("Message received %d" % messageId)
	
		if (messageId in [SOCKET_MESSAGE_INDEX,
						  SOCKET_MESSAGE_BLOCK,
						  SOCKET_MESSAGE_HASHLIST,
						  SOCKET_MESSAGE_STATUS,
						  SOCKET_MESSAGE_TRANSACTIONS_SINCE,
						  SOCKET_MESSAGE_GET_TRANSACTIONS_SINCE,
						  SOCKET_MESSAGE_SYNC_LOCK,
						  SOCKET_MESSAGE_TRANSACTION]):
	
			transid_ = content.readString
			deviceid_ = content.readString
			chainid_ = content.readString
			
			if (self.chainid_ == chainid_):
				
				chain_ = self.chain_
				
				# we only listen to writers for the following information - readers dont inform other of issues
				
				access_ = self.isAccessAllowed(deviceid_)

				if (access_ in [ACCESS_MASTER, ACCESS_PUBLIC, ACCESS_READONLY, ACCESS_READWRITE, ACCESS_WRITEONLY]) and (chain_ != None):
					
					if (messageId == SOCKET_MESSAGE_INDEX):
					
						idx_ = content.readLong
				
						if (chain_.transId != idx_):
							self.log("We are out of sync for chain %s" % (chainid_))
					
					elif (messageId == SOCKET_MESSAGE_HASHLIST):
												
						idx_ = content.readLong
						
						if (idx_ >= chain_.transId) or (access_ == ACCESS_MASTER):
							
							if (idx_ < chain_.transId):
								
								if (access_ == ACCESS_MASTER):
									
									# we need to check here if the origin is correct - ie another master...
									
									if (self.chainmode_ == "m"): # im a master... then notify the responding system they need to update
									
										self.log("Master sync issue - tell master he needs to update via a status message !")
									
										transactionid_ = self.uniqueId

										message_ = MessageWriter()
										message_.writeByte(SOCKET_MESSAGE_STATUS)
										message_.writeString(transactionid_)
										message_.writeString(self.deviceid)
										message_.writeString(self.chainid_)
										message_.writeLong(chain_.transId)
										message_.writeString(chain_.hash)
										message_.writeString(chain_.shadowHash)
									
										socket.send(message_)
											
									else:
										pass # ignore this message as i cant do anything about it !!
									
									return

							# we have a possible agreement or the chain we are talking to has more transactions than us..
						
							count_ = content.readLong
							hashesin_ = []

							if (count_ > 0):
		
								for counter_ in range(0, count_):
									
									hash_ = content.readString
									md5_ = content.readString
									hashesin_.append({"hash":hash_, "md5":md5_})
								
								chainok_ = True
						
								for hashin_ in hashesin_:
									
									hash_ = hashin_["hash"]
									filename_ = chain_.getFullPathForBlock(hash_)
									md5_ = fileio.filemd5(filename_)
									
									if (md5_ != hashin_["md5"]):
										chainok_ = False
										self.logError("Failure in hash %s for chain %s" % (hash_, chainid_))
										self.getBlockForChain(socket, hash_)
										break
									
									else:
										self.log("Hash %s for chain %s OK (md5 = %s)" % (hash_, chainid_, md5_))

								if (chainok_):
									if (self.chainmode_ == "o"):
										
										chain_.reload()										
										partners_ = self.config.partners
										
										if (partners_ != None) and (len(partners_) > 0):
											for partner_ in partners_:
												if (partner_.uid == self.deviceid):
													self.setChainMode(partner_.mode)
										
									else:
										self.log("Chain appears consistent")
										
								else:
									self.log("Chain hash is invalid - resynching chain")
									self.chainmode_ = "o"
									

					elif (messageId == SOCKET_MESSAGE_SYNC_LOCK):
					
						success_ = content.readByte
						
						if (success_ == 1):
							
							self.log("Confirmed synclock from %s" % deviceid_)
							
							self.lock_ = self.deviceid
							transactions_ = self.cachedtransactions_
							self.cachedtransactions_ = []
							self.writeTransactions(transactions_)
					
						else:
							currentlockowner_ = content.readString
					
					elif (messageId == SOCKET_MESSAGE_STATUS):
						
						idx_ = content.readLong
						hash_ = content.readString
						shadowhash_ = content.readString
					
						if (chain_.transId != idx_) or (chain_.hash_ != hash_) or (chain_.shadowHash != shadowhash_):
							
							self.log("We are out of sync for chain %s" % (chainid_))
							self.sendHashRequest(socket)
			
					elif (messageId == SOCKET_MESSAGE_GET_TRANSACTIONS_SINCE):
						
						idx_ = content.readLong
						transactions_ = chain_.getTransactionsFrom(idx_)
						
						if (len(transactions_) > 0):
							
							from modules.customencoder import CustomEncoder
							transactiondata_ = json.dumps(transactions_, cls=CustomEncoder, sort_keys=True)
							
							message_ = MessageWriter()
							message_.writeByte(SOCKET_MESSAGE_TRANSACTIONS_SINCE)
							message_.writeString(transid_)
							message_.writeString(self.deviceid)
							message_.writeString(chainid_)
							message_.writeString(transactiondata_)
							
							socket.send(message_)
							
					elif (messageId == SOCKET_MESSAGE_TRANSACTIONS_SINCE):
					
						transactiondata_ = content.readString
						transactions_ = DAOCollection.fromJson(transactiondata_, ChainEntry)
						
						if (transactions_ != None) and (len(transactions_) > 0):
							shadowhash_, discarded_ = self.writeTransactionsToChain(transactions_, deviceid_)
							
							if (len(discarded_) > 0):
								pass
			
					elif (messageId == SOCKET_MESSAGE_TRANSACTION):
					
						count_ = content.readLong
						transactions_ = []
						
						if (count_ > 0):
							
							for counter_ in range(0, count_):
								json_ = content.readString
								transaction_ = ChainEntry.fromJson(json_)
								
								if (transaction_ != None):
									transactions_.append(transaction_)
					
					elif (messageId == SOCKET_MESSAGE_BLOCK):
						
						hash_ = content.readString
						content_ = content.readBytes
						fileout_ = chain_.getFullPathForBlock(hash_)
								
						with open(fileout_, 'wb') as fileWrite:
							fileWrite.write(content_)
								
						self.log("Written %s for chain %s" % (hash_, chainid_))
						
						# do an integrity check...
						self.sendHashRequest(socket)
			
				else:
					self.log("Not authorized for this action")

			else:
				self.log("Chain id is for %s" % chainid_)
				pass
	

	def notifyReplPartners(self, newHash=None, transIdx=0):
		
		# if this is a read-node only, ignore !!!
		
		myid_ = self.deviceid
		partners_ = []
		
		if (self.chainmode_ in [ACCESS_NONE, ACCESS_READONLY]):
			return
				
		for partner_ in self.config.partners:
			
			if (partner_.uid == myid_):
				pass
			elif (partner_.type != "node"):
				pass
			else:
				partners_.append(partner_.copy())

		if (partners_ != None) and (len(partners_) > 0):
		
			self.log("Notifying replication partners of message")
			self.log("Sending message to %s" % partners_)
				
			chain_ = self.chain_
			transactionid_ = self.uniqueId
			
			message_ = MessageWriter()
			message_.writeByte(SOCKET_MESSAGE_STATUS)
			message_.writeString(transactionid_)
			message_.writeString(self.deviceid)
			message_.writeString(self.chainid_)
			message_.writeLong(transIdx)
			message_.writeString(chain_.hash)
			message_.writeString(newHash)
			
			self.sendMessageToPartners(partners_, message_)


	def shutdown(self):
	
		self.log("Chain shutdown initiated %s" % (self.chainid_))
		self.timer_.stop()


	def __init__(self, chainid=None, manager=None):
		
		# we create a link back to the app for information purposes...
		
		self.cachedtransactions_ = []
		self.connections_ = {}
		self.chainmode_ = "o" # no access
		self.manager_ = manager
		self.chainid_ = chainid
		
		self.log("Creating chain instance = %s" % (chainid))
		
		self.configupdated_ = True
		
		success_ = self.createDirectories()
		
		if (success_):
			
			# for updating the service
			self.timer_ = Repeater(10.0, self.poller, self)
			self.timer_.start()
		
		else:
			self.log("Something wrong with startup - please investigate - %s" % (self.chainid_))



