
import re
import os
import ssl

import urllib
import urllib3
import certifi
import logging

import string, cgi, time
import threading
import json
import base64
import time

import OpenSSL as ssl

from config import *
from modules import *

from .baseapplication import *

from controllers.chaincontroller import *

class DataNodeApplication(BaseApplication):
	
	# vars..
	
	chains_ = None
	server_ = None
	
	
	def __init__(self, appInstance=None):
		
		self.chains_ = {}
		
		BaseApplication.__init__(self, appInstance)

		# we create one listening service for a node - the port ids should never be the same !!

		NotificationCenter().addObserver(NOTIFY_CONFIG_CHANGED, self.configUpdated)

		devicecert_ = ("%s.cer" % self.deviceid)

		self.server_ = SocketServer((self.appInstance.listenon), self.messageReceived, self.deviceConnected, self.deviceDisconnected, devicecert_)


	def deviceConnected(self, socket=None):
	
		pass
	
	def deviceDisconnected(self, socket=None):
		
		pass
	
	def shutdown(self):
	
		BaseApplication.shutdown(self)
	
		self.server_.shutdown()
	

	def chainById(self, chainid=None):
	
		if (chainid != None):
			chainids_ = list(self.chains_.keys())
			if (chainid in chainids_):
				return self.chains_[chainid]

		return None


	def messageReceived(self, messageId, content=None, socket=None):
		
		if (messageId in [SOCKET_MESSAGE_GET_INDEX,
						  SOCKET_MESSAGE_STATUS,
						  SOCKET_MESSAGE_GET_STATUS,
						  SOCKET_MESSAGE_GET_TRANSACTION,
						  SOCKET_MESSAGE_GET_HASHLIST,
						  SOCKET_MESSAGE_GET_BLOCK,
						  SOCKET_MESSAGE_GET_QUERY,
						  SOCKET_MESSAGE_GET_TRANSACTIONS_SINCE,
						  SOCKET_MESSAGE_GET_SYNC_LOCK,
						  SOCKET_MESSAGE_SYNC_RELEASE,
						  SOCKET_MESSAGE_TRANSACTIONS_SINCE,
						  SOCKET_MESSAGE_WRITE_TRANSACTION
						  ]):
						  
			transid_ = content.readString
			deviceid_ = content.readString
			chainid_ = content.readString
			
			chainmgr_ = self.chainById(chainid_)
				
			if (chainmgr_ != None) and (chainmgr_.chain != None):
				
				access_ = chainmgr_.isAccessAllowed(deviceid_)
				chain_ = chainmgr_.chain
	
				if (messageId == SOCKET_MESSAGE_STATUS):
				
					if (access_ in [ACCESS_READONLY, ACCESS_READWRITE, ACCESS_MASTER, ACCESS_PUBLIC]):
				
						idx_ = content.readLong
						hash_ = content.readString
						shadowhash_ = content.readString
							
						self.log("Received a status update for the chain - %d@%s" % (idx_, chainid_))

						if (chain_.transId < idx_):
							
							self.log("Get transactions from %d:%d for chain %s" % (chain_.transId, idx_, chainid_))
							
							message_ = MessageWriter()
							message_.writeByte(SOCKET_MESSAGE_GET_TRANSACTIONS_SINCE)
							message_.writeString(transid_)
							message_.writeString(self.appInstance_.deviceid)
							message_.writeString(chainid_)
							message_.writeLong(chain_.transId)
								
							socket.send(message_)

				elif (messageId == SOCKET_MESSAGE_GET_SYNC_LOCK):
				
					if (access_ == ACCESS_MASTER):

						self.log("Sync-lock requested by %s" % (deviceid_))

						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_SYNC_LOCK)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)

						if (chainmgr_.lock_ == None):
							chainmgr_.lock_ = deviceid_
							message_.writeByte(1)
						
						else:
							# we inform who has the lock if
							message_.writeByte(0)
							message_.writeString(chainmgr_.lock_)
							
						socket.send(message_)
							
				elif (messageId == SOCKET_MESSAGE_SYNC_RELEASE):
				
					if (access_ == ACCESS_MASTER):
				
						if (chainmgr_.lock_ == deviceid_):
							
							self.log("Sync-lock released")
							
							chainmgr_.lock_ = None # clear the lock...
							
							# check if there are transactions to release - if so send them....
							
							if (len(chainmgr_.cachedtransactions_) > 0):
								transactions_ = chainmgr_.cachedtransactions_
								
								chainmgr_.cachedtransactions_ = []
								chainmgr_.writeTransactions(transactions_)
						
				elif (messageId == SOCKET_MESSAGE_GET_INDEX):
					
					if (access_ != ACCESS_NONE):
						
						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_INDEX)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)
						message_.writeLong(chain_.transId)
						message_.writeString(chain_.shadowHash)

						socket.send(message_)
				
					else:
						self.log("Access from an unauthorized node")
							
				elif (messageId == SOCKET_MESSAGE_TRANSACTIONS_SINCE):

					if (access_ != ACCESS_NONE):
						
						transactiondata_ = content.readString
						transactions_ = DAOCollection.fromJson(transactiondata_, ChainEntry)
						
						if (transactions_ != None) and (len(transactions_) > 0):
							shadowhash_, discarded_ = chainmgr_.writeTransactionsToChain(transactions_, deviceid_)
						
				elif (messageId == SOCKET_MESSAGE_GET_TRANSACTIONS_SINCE):
				
					idx_ = content.readLong
					
					if (access_ != ACCESS_NONE):
						
						transactions_ = chain_.getTransactionsFrom(idx_)
						
						if (len(transactions_) > 0):
					
							from modules.customencoder import CustomEncoder
							transactiondata_ = json.dumps(transactions, cls=CustomEncoder, sort_keys=True)
					
							message_ = MessageWriter()
							message_.writeByte(SOCKET_MESSAGE_TRANSACTIONS_SINCE)
							message_.writeString(transid_)
							message_.writeString(self.appInstance_.deviceid)
							message_.writeString(chainid_)
							message_.writeString(transactiondata_)

							socket.send(message_)

				elif (messageId == SOCKET_MESSAGE_GET_STATUS):
				
					if (access_ != ACCESS_NONE):
						
						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_STATUS)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)
						message_.writeLong(chain_.transId)
						message_.writeString(chain_.hash)
						message_.writeString(chain_.shadowHash)

						socket.send(message_)
		
					else:
						self.log("Access from an unauthorized node")

				elif (messageId == SOCKET_MESSAGE_GET_TRANSACTION):
				
					if (access_ in [ACCESS_READONLY, ACCESS_READWRITE, ACCESS_MASTER, ACCESS_PUBLIC]):
					
						recordid_ = content.readLong
						transactions_ = chainmgr_.chain.getTransactionsByIds([recordid_])

						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_TRANSACTION)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)
			
						count_ = len(transactions_)
						message_.writeLong(count_)
						
						if (count_ > 0):
							for transaction_ in transactions_:
								json_ = transaction_.toJson()
								message_.writeString(json_)

						socket.send(message_)

					else:
						self.log("Access from an unauthorized node")

				# write record to chain
		
				elif (messageId == SOCKET_MESSAGE_WRITE_TRANSACTION):

					transactiondata_ = content.readString
					transactions_ = DAOCollection.fromJson(transactiondata_, ChainEntry)
					shadowhash_ = None
				
					if (transactions_ != None) and (len(transactions_) > 0):
						shadowhash_, discarded_ = chainmgr_.writeTransactionsToChain(transactions_, deviceid_)
		
						if (len(discarded_) > 0):
							pass
		
				# get hashes for chain
		
				elif (messageId == SOCKET_MESSAGE_GET_HASHLIST):
				
					if (access_ != ACCESS_NONE):
					
						hashes_ = chain_.hashes()
						info_ = {}
						
						for hash_ in hashes_:
							filename_ = chain_.getFullPathForBlock(hash_)
							md5_ = fileio.filemd5(filename_)
							info_[hash_] = md5_

						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_HASHLIST)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)
						message_.writeLong(chain_.transId)
						
						count_ = len(hashes_)
						
						message_.writeLong(count_)
						
						if (count_ > 0):
							for hash_ in hashes_:
								message_.writeString(hash_)
								message_.writeString(info_[hash_])
			
						socket.send(message_)
					
					else:
						self.log("Access from an unauthorized node")
				
				# request block for chain
		
				elif (messageId == SOCKET_MESSAGE_GET_BLOCK):

					if (access_ in [ACCESS_READONLY, ACCESS_READWRITE, ACCESS_MASTER, ACCESS_PUBLIC]):
						
						chain_ = chainmgr_.chain

						hash_ = content.readString
						filein_ = chain_.getFullPathForBlock(hash_)
						data_ = None
						
						with open(filein_, 'rb') as fileRead:
							data_ = fileRead.read()
						
						if (data_ != None):
							message_ = MessageWriter()
							message_.writeByte(SOCKET_MESSAGE_BLOCK)
							message_.writeString(transid_)
							message_.writeString(self.appInstance_.deviceid)
							message_.writeString(chainid_)
							message_.writeString(hash_)
							message_.writeBytes(data_)

							socket.send(message_)

					else:
						self.log("Access from an unauthorized node")

				elif (messageId == SOCKET_MESSAGE_GET_QUERY):
				
					if (access_ in [ACCESS_MASTER, ACCESS_READWRITE, ACCESS_PUBLIC, ACCESS_READONLY]):
					
						transactions_ = [] # query result comes back here !!
						
						message_ = MessageWriter()
						message_.writeByte(SOCKET_MESSAGE_TRANSACTION)
						message_.writeString(transid_)
						message_.writeString(self.appInstance_.deviceid)
						message_.writeString(chainid_)
						
						count_ = len(transactions_)
						message_.writeLong(count_)
						
						if (count_ > 0):
							for transaction_ in transactions_:
								json_ = transaction_.toJson()
								message_.writeString(json_)
						
						socket.send(message_)
		
					else:
						self.log("Access from an unauthorized node")


	def configUpdated(self, configctl, info):
	
		self.log("Informed that configuration is updated or has loaded!")
		
		chainids_ = list(configctl.chains)
		
		currentchains_ = list(self.chains_.keys())
		toremove_ = list(self.chains_.keys())
		
		if (len(chainids_) > 0):
			
			for chainid_ in chainids_:
				chain_ = None
			
				if (chainid_ not in currentchains_):
					chainctrl_ = ChainController(chainid_, self)
					self.chains_[chainid_] = chainctrl_
				
				else:
					chainctrl_ = self.chains_[chainid_]
					toremove_.remove(chainid_)

				chainctrl_.setConfigUpdated()

		if (len(toremove_) > 0):
			
			for chainid_ in toremove_:
				
				chainctrl_ = self.chains_[chainid_]
				chainctrl_.shutdown()
				
				del self.chains_[chainid_]


