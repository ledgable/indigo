
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
from dataobjects import *
from controllers import *

from .baseapplication import *

class ServiceConnection(TimedSocketConnectionOut):
	
	manager_ = None

	def messageReceived(self, messageId, content=None, socket=None):
	
		self.timer_.lastpoll_ = self.epoch

		if (messageId == SOCKET_MESSAGE_TRANSACTION):
		
			transid_ = content.readString
			chainid_ = content.readString
			count_ = content.readLong
			transactions_ = []
			
			if (count_ > 0):
				
				for counter_ in range(0, count_):
					transactiondata_ = content.readString
					transaction_ = ChainEntry.fromJson(transactiondata_)
					transactions_.append(transaction_)
			
			self.manager_.receivedMessage("transactions", transid_, chainid_, transactions_)
			
		elif (messageId == SOCKET_MESSAGE_HASHLIST):
		
			transid_ = content.readString
			chainid_ = content.readString
			count_ = content.readLong
			hashes_ = []
				
			if (count_ > 0):
				for counter_ in range(0, count_):
					hash_ = content.readString
					md5_ = content.readString
					hashes_.append({"hash":hash_, "md5":md5_})
					
			self.manager_.receivedMessage("hashlist", transid_, chainid_, hashes_)

		else:
			
			self.log("Received message %d" % messageId)


	def connectSuccess(self, socket=None):
		
		self.log("Connect received to service !!")
	

	def disconnected(self, socket):
		
		SocketConnectionOut.disconnected(self, socket)
		
		self.manager_.removeConnection(self)


	def disconnectSuccess(self, socket=None):
		
		self.log("Disconnect received")


	def failedToConnect(self, socket=None):
		
		self.log("Disconnect received")

		self.manager_.removeConnection(self)


	def __init__(self, manager, uid=None, destination=None):

		self.manager_ = manager
		
		SocketConnectionOut.__init__(self, destination, self.messageReceived, self.connectSuccess, self.disconnectSuccess, self.failedToConnect)


class ConsoleApplication(BaseApplication):

	connections_ = None


	def removeConnection(self, connection=None):
	
		connectids_ = list(self.connections_.keys())
		connectid_ = connection.key_
	
		if (connectid_ in connectids_):
			
			messages_ = connection.messages
			self.log("Removed connection from platform due to disconnect")

			del self.connections_[connectid_]

			if (len(messages_) > 0):
				self.log("Still have messages in the pipeline for this channel")


	def nodesForChain(self, chainid, modesrequired=["m"]):
	
		config_ = self.configctrl_.configForChain(chainid)
		nodes_ = []
		
		if (config_ != None):
			partners_ = config_.partners

			for partner_ in partners_:
				if (partner_.mode in modesrequired) and (partner_.type == "node"):
					nodes_.append(partner_)

		return nodes_


	def recv_transactions(self, transactionid, chainid=None, transactions=None):

		config_ = self.configctrl_.configForChain(chainid)
		
		self.out("")
		self.out("Transactions for %s" % transactionid)
		self.out(("-"*(120)))
	
		for transaction_ in transactions:
			self.out("%s - %s" % (transaction_.md5hash(), transaction_.toJson()))

		self.out("")
		self.out("The command completed successfully")


	def recv_hashlist(self, transactionid, chainid=None, hashes=None):
	
		self.out("")
		self.out("%-34s %-20s %-10s %8s" % ("HashId", "", "", ""))
		self.out(("-"*60))
		
		for hash_ in hashes:
			self.out("%-34s %-20s %-10s %8s" % (hash_, "", "", ""))
	
		self.out("")
	
		return True
	
	
	def receivedMessage(self, messageid, *params):
	
		functionname_ = ("recv_%s" % messageid)
		
		try:
			if (hasattr(self, functionname_)):
				
				self.out("")
				
				functiontocall_ = getattr(self, functionname_)
				success_ = functiontocall_(*params)
						
		except Exception as inst:
			self.logException(inst)


	def getTransaction(self, chainid=None, recordid=0):

		nodes_ = self.nodesForChain(self.appInstance.chainid, ["r", "rw", "w", "m"])
	
		if (len(nodes_) > 0):
		
			node_ = nodes_[0]
		
			connection_ = None
			connectids_ = list(self.connections_.keys())
			
			if (node_.uid in connectids_):
				
				# connection already created....
				connection_ = self.connections_[node_.uid]
				
				# get hashes !!
				transactionid_ = self.uniqueId

				newmessage_ = MessageWriter()
				newmessage_.writeByte(SOCKET_MESSAGE_GET_TRANSACTION)
				newmessage_.writeString(transactionid_)
				newmessage_.writeString(self.appInstance.deviceid)
				newmessage_.writeString(self.appInstance.chainid)
				newmessage_.writeLong(recordid)

				connection_.send(newmessage_)
		
				return True, ("Request dispatched with transaction id %s" % (transactionid_))
			
			else:
				# need to create connection to service
				connection_ = ServiceConnection(self, node_.uid, node_.ip_address)
				self.connections_[node_.uid] = connection_
				
			return False, "Connection not ready"

		return False, "No nodes for requested chain available"


	def getHashes(self, chainid=None):
	
		nodes_ = self.nodesForChain(self.appInstance.chainid, ["r", "rw", "w", "m"])
	
		if (len(nodes_) > 0):
	
			node_ = nodes_[0]

			connection_ = None
			connectids_ = list(self.connections_.keys())

			if (node_.uid in connectids_):
				
				# connection already created....
				connection_ = self.connections_[node_.uid]
					
				# get hashes !!
				transactionid_ = self.uniqueId
					
				newmessage_ = MessageWriter()
				newmessage_.writeByte(SOCKET_MESSAGE_GET_HASHLIST)
				newmessage_.writeString(transactionid_)
				newmessage_.writeString(self.appInstance.deviceid)
				newmessage_.writeString(self.appInstance.chainid)
				
				connection_.send(newmessage_)
		
				return True, ("Request dispatched with transaction id %s" % (transactionid_))
					
			else:
				# need to create connection to service
				connection_ = ServiceConnection(self, node_.uid, node_.ip_address)
				self.connections_[node_.uid] = connection_
					
				return False, "Connection not ready"

		return False, "No nodes for requested chain available"


	def writeRecords(self, records=None):
	
		nodes_ = self.nodesForChain(self.appInstance.chainid, "m")
		
		if (len(nodes_) > 0):
			
			if (records != None) and (len(records) > 0):
				
				self.log("Masters = %s" % nodes_)
				node_ = nodes_[0]
	
				connection_ = None
				connectids_ = list(self.connections_.keys())
				
				if (node_.uid in connectids_):
					# connection already created....
					connection_ = self.connections_[node_.uid]
				
				else:
					# need to create connection to service
					connection_ = ServiceConnection(self, node_.uid, node_.ip_address)
					self.connections_[node_.uid] = connection_

				if (connection_ != None):
					
					jsondata_ = records.toJson()
					
					transactionid_ = self.uniqueId
					
					newmessage_ = MessageWriter()
					newmessage_.writeByte(SOCKET_MESSAGE_WRITE_TRANSACTION)
					newmessage_.writeString(transactionid_)
					newmessage_.writeString(self.appInstance.deviceid)
					newmessage_.writeString(self.appInstance.chainid)
					newmessage_.writeString(jsondata_)
					
					connection_.send(newmessage_)

					return True, ("Transaction %s dispatched" % (transactionid_))
				
				else:
					return False, ("No connection to service available")
			
			else:
				return False, "No records to write"

		return False, "No nodes for requested chain available"


	def cmd_use(self, commandparts=None):
	
		chainid_ = None
		
		if (len(commandparts) == 2):
			
			chainid_ = commandparts[1]
			chainids_ = list(self.configctrl_.chains)
			
			if (chainid_ in chainids_):
				
				if (chainid_ != self.appInstance.chainid_):
					self.appInstance.chainid_ = chainid_
					return True, ("Chain Switched to %s" % chainid_)
						
				else:
					return False, ("Already using chain")
								
			else:
				
				return False, ("Chain %s does not exist" % (chainid_))
		
		return False, "Syntax Error"


	def cmd_query(self, commandparts=None):
		
		if (len(commandparts) >= 2):
		
			mode_ = commandparts[1]
		
			if (mode_ == "hashes"):
		
				return self.getHashes(self.appInstance.chainid)
		
			elif (mode_ == "record"):
				
				if (len(commandparts) >= 3):
					
					querytype_ = commandparts[2]
				
					if (querytype_ == "last"):
						return True, "Not implemented yet"

					elif (querytype_ == "since"):
						return True, "Not implemented yet"

					else:
						recordid_ = int(querytype_)
						return self.getTransaction(self.appInstance.chainid, recordid_)
		
				else:
					return False, "Syntax Error"

			elif (mode_ == "match"):
				return True, "Not implemented yet"
			
			else:
				return False, ("Unknown mode - %s" % (mode_))

		return False, "Syntax Error"


	def cmd_insert(self, commandparts=None):
		
		datatowrite_ = " ".join(commandparts[1:])
		
		if (datatowrite_ != "") and (datatowrite_ != None):
			
			firstchar_ = datatowrite_[0:1]
			
			if (firstchar_ in ["{", "["]):
				
				records_ = None
				jsondata_ = json.loads(datatowrite_)
				
				if (jsondata_ != None):
					
					# push this into an list structure regardless
					
					if (firstchar_ == "{"):
						records_ = DAOCollection([jsondata_])
					
					elif (firstchar_ == "["):
						records_ = DAOCollection(jsondata_)
					
					return self.writeRecords(records_)
	
		return False, "JSON data invalid"


	def cmd_help(self, commandparts=None):
	
		url_ = self.appInstance.root_ + "/text/consoleinfo_en.txt"
		content_ = ""
				
		with open(url_, 'r', encoding=UTF8) as fileRead:
			content_ = fileRead.read()
						
		for textcontent_ in content_.split("\n"):
			self.out(textcontent_)

		return True, "Command completed successfully"


	def cmd_connections(self, commandparts=None):
		
		connectionids_ = list(self.connections_.keys())
		
		self.out("%-34s %-20s %-10s %8s" % ("Connection", "Destination", "", "Idle"))
		self.out(("-"*120))
		
		now_ = self.epoch
		
		for connectionid_ in connectionids_:
			connection_ = self.connections_[connectionid_]
			idle_ = (now_ - connection_.timer_.lastpoll_)
			self.out("%-34s %-20s %-10s %8d" % (connection_.key_, connection_.destination_, "", idle_))
	
		self.out("")

		return True, "Command completed successfully"


	def cmd_describe(self, commandparts=None):
	
		config_ = self.configctrl_.configForChain(self.appInstance.chainid_)
			
		if (config_ != None):
				
			structure_ = config_.structure
					
			self.out("%-5s %-20s %-10s %8s" % ("Pos", "Structure", "Datatype", "Length"))
			self.out(("-"*60))
					
			for structureitem_ in structure_:
				self.out("%-5s %-20s %-10s %8d" % (structureitem_.position, structureitem_.field_name, structureitem_.datatype, int(structureitem_.length)))
			
			self.out("")

			return True, "Command completed successfully"
				
		return False, "No chain selected"


	def cmd_show(self, commandparts=None):
	
		if (len(commandparts) == 2):
			
			mode_ = commandparts[1]
	
			if (mode_ in ["chains"]):
		
				if (mode_ == "chains"):
			
					chainids_ = list(self.configctrl_.chains)
			
					self.out("%-2s %-34s %-20s %-10s %8s" % ("","ChainId", "", "", ""))
					self.out(("-"*60))
				
					for chainid_ in chainids_:
						selected_ = ""
						if (chainid_ == self.appInstance.chainid_):
							selected_ = "*"
						self.out("%-2s %-34s %-20s %-10s %8s" % (selected_, chainid_, "", "", ""))
		
					self.out("")

					return True, "Command completed successfully"
							
			return False, ("Mode %s is invalid" % (mode_))
				
		return False, "Syntax Error"


	def doConsole(self):

		self.stdout.write("\n")
		
		doprompt_ = True
		command_ = ""
		
		self.out("Commands should be terminated by a ';' character")
		
		while (True):
			
			prompt_ = ("\n\033[36mcql %s \033[0m> " % self.appInstance.chainid)
			commandin_ = input(prompt_)
			
			lines_ = commandin_.split("\n")
			
			for line_ in lines_:
				
				if (len(line_) > 0):
					
					if (line_[-1:1] == "\n"):
						line_ = line_[0:-1]
					
					command_ += line_
					lastchar_ = command_[-1:]
					
					if (lastchar_ == ";"):
					
						command_ = command_[0:-1]
						commandparts_ = command_.split(" ")
						
						syntaxmsg_ = ""
						syntaxerror_ = False
						
						if (len(commandparts_) > 0):
							
							commandroot_ = commandparts_[0].lower()
							
							if (commandroot_ in ['quit', 'exit']):
								self.out("Quitting - Bye")
								os._exit(0)
						
							elif (commandroot_[0:1] == "#"):
								
								rawrecordid_ = commandroot_[1:]
								
								if (rawrecordid_ != None) and (rawrecordid_ != ""):
									
									try:
										recordid_ = int(rawrecordid_)
										success_, message_ = self.getTransaction(self.appInstance.chainid, recordid_)

									except Exception as inst:
										success_, message_ = (False, "Unknown record id")

								else:
									success_, message_ = (False, "Unknown record id")

								command_ = ""

							else:
								
								functionname_ = ("cmd_%s" % commandroot_)
							
								try:
									if (hasattr(self, functionname_)):
										
										self.out("")
										
										functiontocall_ = getattr(self, functionname_)
										success_, message_ = functiontocall_(commandparts_)
										
										if (success_):
											self.out(message_)
										else:
											self.out("%s - try 'help' for further information" % (message_))
							
									else:
										self.out("No such command - try 'help' for further information")

								except Exception as inst:
									self.logException(inst)

								command_ = ""


	def __init__(self, appInstance=None):
	
		self.connections_ = {}
		
		BaseApplication.__init__(self, appInstance)
	
		self.doConsole()


	def configUpdated(self):

		self.log("Informed that configuration is updated or has loaded!")

		chainids_ = list(self.configctrl_.chains)
		
		self.log("Chains = %s" % (chainids_))
