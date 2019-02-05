
	# file/directory structure for configcontroller

	# + ---- __data (MAIN DATA DIRECTORY)
	# 		 |---- deviceid
	# 		 	   |---- config
	#        	   		 |---- node_xxxxx.json (json config for node)
	# 		 	   |---- <nodeid>
	#       	   		 |---- cache (for caching inbound changes)
	#         	   		 	   |---- cache_yyyy.chc (cache file for update to chain to be added (yyyy transaction id)
	#       	   		 |---- data (for chains under the nodeid)
	#         	  		 	   |---- xxx (directory for chain blocks (first 3 hex chars)
	#         				   		 |---- blk_xxxyyyy (chain block xxxyyyy for chain)

	# modification to this structure is highly critical and may result in service failure

	# Notes
	#
	# You can create a symbolic link to the __data directory (on another volume) with a separate backup strategy

from modules import *

class ConfigController(BaseClass, metaclass=Singleton):

	manager_ = None
	connectionconfig_ = None
	config_ = None
	timer_ = None
	
	
	@property
	def config(self):
		return self.config_


	@property
	def chains(self):
		return list(self.config_.keys())


	@property
	def root(self):
		return self.manager_.root_


	def configForChain(self, chainid):
	
		if (chainid in self.chains):
			return self.config_[chainid]
	
		return None


	def findPartners(self, permissionset=[], chainid=None, type="node"):
		
		config_ = self.configForChain(chainid)
		possibles_ = []

		if (config_ != None):
			partners_ = config_.partners
			
			if (partners_ != None) and (len(partners_) > 0):
				
				for partner_ in partners_:
					if (partner_.uid != self.manager_.appInstance.deviceid):
						if (partner_.type == type) or (type == "all"):
							if (partner_.mode in permissionset):
								possibles_.append(partner_.copy())
		
		return possibles_


	def loadConfig(self):
	
		directory_ = self.manager_.configdir
	
		if os.path.exists(directory_):
			
			configchanged_ = False
			
			for configfile_ in os.listdir(directory_):

				chainid_ = configfile_[6:-5]
				newchain_ = None

				url_ = directory_ + "/" + configfile_

				with open(url_, 'r', encoding=UTF8) as fileRead:
					jsondata_ = json.load(fileRead)
					newchain_ = DAOObject(jsondata_)
			
				if (newchain_ != None):
					configchanged_ = True
					self.log("Found chain = %s" % chainid_)
					self.config_[chainid_] = newchain_

			if (configchanged_):
				NotificationCenter().postNotification(NOTIFY_CONFIG_CHANGED, self, None)


	def commitConfig(self, config=None):
	
		if (config == None):
			return
				
		keys_ = list(config.keys())
		directory_ = self.manager_.configdir
		root_ = self.root

		for chainid_ in keys_:
			
			chain_ = config[chainid_]
			
			if (chain_.is_deleted == 1):

				# delete config file
				configfile_ = directory_ + ("/chain_%s.json" % chainid_)
				
				if (os.path.exists(configfile_)):
					os.remove(configfile_)

				# now delete chain directory
				chaindir_ = self.manager_.devicedir + ("/%s" % chainid_)
				
				if (os.path.exists(chaindir_)):
					os.rmtree(chaindir_)
		
				# delete the config from the config to load
				del config[chainid_]
				
				self.log("Chain %s deleted" % chainid_)

			else:
				
				# write the config to a json file in the config directory
				jsonstring_ = chain_.toJson()
				
				self.log("Writing config for chain %s" % chainid_)
				
				fileoutconfig_ = directory_ + ("/chain_%s.json" % chainid_)
				
				with open(fileoutconfig_, 'w', encoding=UTF8) as fileWrite:
					fileWrite.write(("%s" % jsonstring_))

				if (chain_.publickey != None and chain_.privatekey != None):
					
					pemfile_ = chain_.privatekey + chain_.publickey					
					fileoutcert_ = root_ + ("/certs/%s.cer" % chainid_)

					with open(fileoutconfig_, 'w', encoding=UTF8) as fileWrite:
						fileWrite.write(("%s" % jsonstring_))
			
		
		self.config_ = DAOObject(config)
		
		NotificationCenter().postNotification(NOTIFY_CONFIG_CHANGED, self, None)


	def forNode(self, nodeid=None):
	
		if (nodeid != None):
			if (nodeid in list(self.config_.keys())):
				return self.config_[nodeid]

		return None


	@property
	def deviceid(self):
		return self.manager_.deviceid


	def sendGetConfig(self, socket=None):
	
		if (socket != None):
			messageid_ = self.uniqueId
			
			message_ = MessageWriter()
			message_.writeByte(SOCKET_MESSAGE_GET_CONFIG)
			message_.writeString(messageid_)
			
			socket.send(message_)


	def messageReceived(self, messageId, content=None, socket=None):
		
		if (messageId == SOCKET_MESSAGE_REGISTER):
	
			transid_ = content.readString
			success_ = content.readByte
			reason_ = content.readString

			if (success_ == 1):
				self.log("Device Registered - %s" % (reason_))
				self.sendGetConfig(socket)
	
			else:
				self.logError("Device Not Registered - Reason = %s" % (reason_))

				self.connectionconfig_.disconnect()
				os._exit(0)

		elif (messageId == SOCKET_MESSAGE_CONFIG):
			
			transid_ = content.readString
			root_ = self.root

			privatekey_ = content.readString
			publickey_ = content.readString
			
			if (publickey_ != None and privatekey_ != None):
				
				pemfile_ = privatekey_ + publickey_
				fileoutcert_ = root_ + ("/certs/%s.cer" % self.deviceid)
					
				with open(fileoutcert_, 'w', encoding=UTF8) as fileWrite:
					fileWrite.write(pemfile_)

			
			chaincount_ = content.readInt
			
			config_ = {}

			# count is kinda like success = 0 is no config / fail
			
			if (chaincount_ > 0):
				
				for chain_ in range(0, chaincount_):
					
					chain_ = DAOObject({})
					
					setattrs(chain_,
							 uid = content.readString,
							 is_deleted = content.readByte,
							 structure = json.loads(content.readString)
							 )
							 
					partnercount_ = content.readInt
					partners_ = []
			
					for partner_ in range(0, partnercount_):
						
						partner_ = DAOObject({})
						
						setattrs(partner_,
								 uid = content.readString,
								 ip_address = content.readString,
								 mode = content.readString,
								 type = content.readString
								 )

						privatekey_ = content.readString
						publickey_ = content.readString
		
						if (publickey_ != None and privatekey_ != None):
			
							pemfile_ = privatekey_ + publickey_
							fileoutcert_ = root_ + ("/certs/%s.cer" % partner_.uid)
				
							with open(fileoutcert_, 'w', encoding=UTF8) as fileWrite:
								fileWrite.write(pemfile_)
								
						partners_.append(partner_)
	
					chain_.partners = partners_
					
					config_[chain_.uid] = chain_
								
				self.commitConfig(config_)

				socket.socketDisconnect("Local Disconnect Req")

		else:
			
			self.log("Unknown message = %s" % content)


	def connectSuccess(self, socket=None):
	
		self.log("Connect received")
	
		systemtype_ = sys.platform
		transid_ = self.uniqueId
		serviceid_ = RawVars().serviceid
		
		self.log("Using serviceid = %s" % serviceid_)
		
		message_ = MessageWriter()
		message_.writeByte(SOCKET_MESSAGE_REGISTER)
		
		message_.writeString(transid_)
		message_.writeString(self.deviceid)
		message_.writeString(self.manager_.devicepin)
		message_.writeString("node")
		message_.writeString(serviceid_)

		addressparts_ = ("0.0.0.0", 0)

		if (self.manager_.register != "0.0.0.0"):
			parts_ = self.manager_.register.split(":")
			
			if (len(addressparts_) == 2):
				addressparts_ = (parts_[0], int(parts_[1]))

		else:
			parts_ = self.manager_.listenon.split(":")
			if (len(parts_) == 2):
				addressparts_ = ("0.0.0.0", int(parts_[1]))

		message_.writeString(addressparts_[0])
		message_.writeInt(addressparts_[1])

		message_.writeString(systemtype_)
		message_.writeInt(DATANODE_VERSION)

		socket.send(message_)


	def disconnectSuccess(self, socket=None):
	
		self.log("Disconnect received")
	
		self.connectionconfig_ = None


	def pollForConfig(self, args=None):
		
		# check for config update...
	
		if (self.connectionconfig_ == None):
			self.connectionconfig_ = TimedSocketConnectionOut(None, self.destination_, self.messageReceived, self.connectSuccess, self.disconnectSuccess, None, "indexer.pem")


	def shutdown(self):

		self.timer_.stop()


	def start(self):
		
		self.loadConfig()
		
		# set up a poller for 25 minute intervals
		
		if (self.timer_ == None):
			self.timer_ = Repeater(1500.0, self.pollForConfig, self)
			self.timer_.start()
		
		# get the initial config !
		
		self.pollForConfig(None)
		

	def __init__(self, manager=None, destination=None):
		
		self.config_ = {}
		self.destination_ = destination
		self.manager_ = manager

