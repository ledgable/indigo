
import zlib

from struct import *
from config import *

from OpenSSL import SSL

from twisted.internet.protocol import Factory, ServerFactory, Protocol, ClientFactory
from twisted.internet.endpoints import SSL4ClientEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor
from twisted.internet import ssl as tSSL
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.defer import setDebugging

from threading import Timer
from threading import Thread

from .repeater import *
from .baseclass import *
from .datamgmt import *
from .ipblocker import *

	# Some considerations
	# - Each node has one listening server
	# - Each node has multiple client connections to known services
	# - The configuation is managed via the central nexus (ledgable.com)

	# The socket manager (client and server) are designed to pass up a message
	# (other than connect/disconnect) to the corresponding service manager - via the fnmessage mechanism

	# The server is a central mechanism that any inbound communication is allowed to happen / from who (kind of an
	# unofficial firewall implementation per se)

	# all intra-node messages are compressed (using zlib compression)

# we wrap the connection object cause we want to know when things work / fail

def myConnectProtocol(endpoint, protocol, onConnect, onFail):

	class OneShotFactory(Factory):
		def buildProtocol(self, addr):
			return protocol

	d = endpoint.connect(OneShotFactory())

	if (onConnect):
		d.addCallback(onConnect)

	if (onFail):
		d.addErrback(onFail)

	return d


class SocketProtocol(Protocol, BaseClass):
	
	socketmgr_ = None
	inbuffer_ = b""
	uid_ = None
	deviceid_ = None


	@property
	def ipAddress(self):
		if (self.transport != None):
			peer_ = self.transport.getPeer()
			return peer_.host
		return None


	@property
	def uid(self):
		return self.uid_


	def __init__(self, socketmgr=None):
		
		self.uid_ = self.uniqueId
		self.socketmgr_ = socketmgr
		
		self.log("Created Channel Protocol")


	def dataReceived(self, data):
		
		self.inbuffer_ += data
		
		while(True):
			
			if (len(self.inbuffer_) < 4):
				return
			
			msglen_ = unpack('!I', self.inbuffer_[:4])[0]
			
			if (len(self.inbuffer_) < msglen_):
				return
		
			messagestring_ = self.inbuffer_[4:msglen_+4]
			self.inbuffer_ = self.inbuffer_[msglen_+4:]
			
			decompressed_ = zlib.decompress(messagestring_)
			message_ = MessageReader(decompressed_)
			
			self.processMessage(message_)


	def connectionMade(self):
		
		if (self.socketmgr_ == None):
			self.socketmgr_ = self.factory
			self.socketmgr_.socketConnected(self)
		
		else:
			self.socketmgr_.protocol_ = self
			self.log("Connection made to service '%s' - awaiting ready notification" % self.socketmgr_.destination_)


	def connectionLost(self, reason):
		
		self.log("Connection lost")
		
		if (self.socketmgr_):
			self.socketmgr_.disconnected(self)


	def connectionFailed(self):
		
		if (self.socketmgr_):
			self.socketmgr_.protocol_ = self
				
		self.log("Connection failed to service '%s' - cleaning up" % self.socketmgr_.destination_)
		
		if (self.socketmgr_):
			self.socketmgr_.disconnect()


	def send(self, message): # send data to socket !! Very important function
				
		data_ = message.data
		compressed_ = zlib.compress(data_)
		msglen_ = pack('!I', len(compressed_))
					
		if (self.transport == None):
			self.log("Transport is unavailable for '%s' - major issue !" % self.socketmgr_.destination_socketmgr_)
		
		else:
			self.transport.write(msglen_)
			self.transport.write(compressed_)


	def socketConnected(self, message):
	
		transid_ = message.readString
		version_ = message.readString
		api_ = message.readInt
		sessionid_ = message.readString
		
		if (api_ > SOCKET_API_VERSION):
			self.log("API of server is higher than my version - please update your client !!")
			self.transport.loseConnection()
			return
		
		else:
			messageOut_ = {"trans":transid_, "version":version_, "api":api_, "sessionid":sessionid_}

		self.log("Received connection message %s" % (messageOut_))
		self.socketmgr_.connected_ = True
		self.socketmgr_.connectionEstablished(self)


	def socketDisconnect(self, message):
	
		self.socketmgr_.connected_ = False
		peer_ = self.transport.getPeer()
		
		self.log("Received remote message from '%s' to disconnect channel !" % (peer_))
				
		self.socketmgr_.disconnect()


	def processMessage(self, message):
		
		messageId = message.readByte
				
		if (messageId == SOCKET_MESSAGE_READY):
			return self.socketConnected(message)
	
		elif (messageId == SOCKET_MESSAGE_DISCONNECT):
			return self.socketDisconnect(message)
		
		else:
			self.socketmgr_.processMessage(messageId, message, self)


	def shutdown(self, args=None):

		self.socketDisconnect("Shutdown initiated")

		if (self.transport != None):
			self.transport.loseConnection()

class SocketConnectionOut(BaseClass):
	
	connected_ = False
	destination_ = None
	protocol_ = None
	endpoint_ = None
	messagestosend_ = None
	certificate_ = None
	certroot_ = os.path.dirname(os.path.abspath(__file__)) + "/../certs"

	fnconnect_ = None
	fndisconnect_ = None
	fnfailed_ = None
	key_ = None
	
	@property
	def messages(self):
		return self.messagestosend_

	def __init__(self, destination=None, fnmessage=None, fnconnect=None, fndisconnect=None, fnfailed=None, certificate=None):

		self.destination_ = destination
		self.messagestosend_ = []
		
		self.fnmessage_ = fnmessage
		self.fnconnect_ = fnconnect
		self.fndisconnect_ = fndisconnect
		self.fnfailed_ = fnfailed
		self.certificate_ = certificate
		
		self.log("connecting to %s" % destination)
		
		self.connect()


	def send(self, message=None):
		
		if (self.protocol_ != None) and (message != None):
			if (self.connected_):
				reactor.callFromThread(self.protocol_.send, message)
			
		elif (message != None):
			self.messagestosend_.append(message)


	def connect(self):
		
		if (self.destination_ == None):
			return
				
		addressparts_ = self.destination_.split(":")
		self.log("Establishing socket destination '%s'" % (addressparts_))

		try:
			
			sslcontext_ = None
			
			if (self.certificate_):
				file_ = ("%s/%s" % (self.certroot_, self.certificate_))

				if (os.path.exists(file_)):
					self.log("Using ssl certificate %s" % file_)
					sslcontext_ = tSSL.DefaultOpenSSLContextFactory(file_, file_, sslmethod=SSL.TLSv1_2_METHOD)
		
					context_ = sslcontext_.getContext()
					context_.set_options(SSL.TLSv1_2_METHOD | SSL.OP_NO_COMPRESSION | SSL.OP_CIPHER_SERVER_PREFERENCE)
					context_.set_cipher_list(SSL_CIPHERS)
		
			if (sslcontext_ != None):
				self.endpoint_ = SSL4ClientEndpoint(reactor, addressparts_[0], int(addressparts_[1]), sslcontext_, timeout=2)
			
			else:
				self.endpoint_ = TCP4ClientEndpoint(reactor, addressparts_[0], int(addressparts_[1]), timeout=2)

			reactor.callFromThread(myConnectProtocol, self.endpoint_, SocketProtocol(self), self.serviceConnected, self.serviceFailed)

		except Exception as inst:
			self.logException(inst)
			
			self.disconnected(self.protocol_)


	def serviceConnected(self, *args):
	
		self.log("Connected to endpoint '%s'" % (self.destination_))
	

	def serviceFailed(self, err):
	
		self.endpoint_ = None
		self.logError("Failed to connect to endpoint '%s'" % (self.destination_))
		
		if (self.fnfailed_):
			self.fnfailed_(self)


	def processMessage(self, messageId, content, socket=None):
		
		try:
			if (self.fnmessage_):
				self.fnmessage_(messageId, content, socket)
			
			else:
				self.log("No handler for message received %d" % (messageId))
	
		except Exception as exception:
			self.logException(exception)


	def connectionEstablished(self, socket):
		
		self.log("Connected to '%s' - ready to send messages !" % (self.destination_))
	
		if (self.fnconnect_):
			self.fnconnect_(socket)
		else:
			self.log("No handler for connected")

		if (len(self.messagestosend_) > 0):
			
			messages_ = list(self.messagestosend_)
			self.messagestosend_ = []
			
			while (len(messages_) > 0):
				message_ = messages_[0]
				del messages_[0]
				self.send(message_)


	def disconnected(self, socket):
		
		self.endpoint_ = None
		
		if (self.protocol_ != None):
			self.log("Socket protocol disconnect received")
			self.protocol_ = None

		if (self.fndisconnect_):
			self.fndisconnect_(socket)
		else:
			self.log("No handler for disconnect")


	def disconnect(self):
		
		self.log("Socket Disconnected from '%s'" % (self.destination_))
		self.endpoint_ = None
		
		self.log("Foribly terminating connection to service '%s'" % self.destination_)
		
		self.shutdown()
	
	def shutdown(self):

		if (self.protocol_ != None):
			self.protocol_.transport.loseConnection() # terminate connection immediately !


class TimedSocketConnectionOut(SocketConnectionOut):

	timer_ = None
	
	
	def send(self, message=None):
	
		self.timer_.lastpoll_ = self.epoch
		SocketConnectionOut.send(self, message)


	def poller(self, args=None):
		
		now_ = self.epoch
		
		if (self.timer_.lastpoll_ < (now_ - 120)):
			self.timer_.stop()
			reactor.callFromThread(self.shutdown)
	

	def __init__(self, keyid=None, destination=None, fnmessage=None, fnconnect=None, fndisconnect=None, fnfailed=None, certificate=None):
		
		self.key_ = keyid
		
		self.timer_ = Repeater(20.0, self.poller, self)
		self.timer_.lastpoll_ = self.epoch
		
		self.timer_.start()

		SocketConnectionOut.__init__(self, destination, fnmessage, fnconnect, fndisconnect, fnfailed, certificate)


class SocketConnectionIn(ServerFactory, BaseClass):

	listenon_ = None
	manager_ = None
	protocol_ = None
	connections_ = None
	

	def __init__(self, listenon, manager=None):
		self.connections_ = []
		self.listenon_ = listenon
		self.manager_ = manager
		self.protocol = SocketProtocol
	

	def find(self, deviceid=None):
		
		if (deviceid == None):
			return None

		if (len(self.connections_) > 0):
			for connection_ in self.connections_:
				if (connection_.deviceid_ == deviceid):
					return connection_
	
		return None


	def connectionLost(self, protocol):
		
		counter_ = 0
		
		for existingdevice_ in self.connections_:
			
			if (existingdevice_ == protocol):
				
				self.log("Removed socket due to disconnect")
				connection_ = self.connections_[counter_]
				del self.connections_[counter_] # remove the user from the active users list...
				connection_.shutdown()
				connection_ = None
				break
			
			counter_ += 1


	def disconnected(self, socket):
		
		self.log("Socket protocol disconnect received")
		
		self.connectionLost(socket)
	
		if (self.manager_.fndisconnect_):
			self.manager_.fndisconnect_(socket)
		else:
			self.log("No handler for disconnect")


	def disconnect(self):
		
		self.connectionLost(self.protocol_)


	def acceptConnection(self, socket=None):
	
		peer_ = socket.transport.getPeer()
		ipaddress_ = peer_.host
		
		success_, countrycode_ = IPBlocker().check(ipaddress_, "socket")
		
		return success_


	def socketConnected(self, newsocket):
		
		self.connections_.append(newsocket)
		
		if (not self.acceptConnection(newsocket)):
			newsocket.transport.loseConnection()
			return
		
		self.log("Socket connected")

		message_ = MessageWriter()
		message_.writeByte(SOCKET_MESSAGE_READY)
		message_.writeString(NULL_VAR)
		message_.writeString(SOCKET_SERVER_VERSION)
		message_.writeInt(SOCKET_API_VERSION)
		message_.writeString(newsocket.uid) # uniqueid for connection...
		
		newsocket.send(message_)


	def connectionEstablished(self, socket):
	
		self.log("Connected to '%s' - ready to send messages !" % (self.destination_))
	
		if (self.manager_.fnconnect_):
			self.manager_.fnconnect_(socket)
		else:
			self.log("No handler for connected")


	def processMessage(self, messageId, content, socket=None):
		
		try:
			if (self.manager_.fnmessage_):
				self.manager_.fnmessage_(messageId, content, socket)
			else:
				self.log("No handler for message received %d" % (messageId))
		
		except Exception as exception:
			self.logException(exception)


# outbound client socket connection to a server
class SocketClient(SocketConnectionOut):
	
	def __init__(self, destination=None, fnmessage=None):
		SocketConnectionOut.__init__(self, destination, fnmessage)



# server client channel manager
class SocketServer(BaseClass):

	listenon_ = None
	fnmessage_ = None
	fnconnect_ = None
	fndisconnect_ = None
	factory_ = None
	certificate_ = None
	certroot_ = os.path.dirname(os.path.abspath(__file__)) + "/../certs"

	def disconnected(self):
	
		pass


	def socketConnected(self, newsocket):
	
		pass


	def __init__(self, listenon=None, fnmessage=None, fnconnect=None, fndisconnect=None, certificate=None):
		
		self.listenon_ = listenon
		self.fnmessage_ = fnmessage
		self.fnconnect_ = fnconnect
		self.fndisconnect_ = fndisconnect
		self.certificate_ = certificate
		self.create()


	def shutdown(self):
	
		self.log("Shutting down reactor")
	
		reactor.callFromThread(reactor.stop)
	

	def create(self):
		
		if (self.listenon_ == None):
			return
	
		addressparts_ = self.listenon_.split(":")
		
		self.log("Establishing socket server at '%s'" % (self.listenon_))
		
		try:
			self.factory_ = SocketConnectionIn(self.listenon_, self)
			sslcontext_ = None
			
			if (self.certificate_ != None):
				
				if (self.certificate_):
					file_ = ("%s/%s" % (self.certroot_, self.certificate_))

					if (os.path.exists(file_)):
						self.log("Using ssl certificate %s" % file_)
						sslcontext_ = tSSL.DefaultOpenSSLContextFactory(file_, file_, sslmethod=SSL.TLSv1_2_METHOD)
	
						context_ = sslcontext_.getContext()
						context_.set_options(SSL.TLSv1_2_METHOD | SSL.OP_NO_COMPRESSION | SSL.OP_CIPHER_SERVER_PREFERENCE)
						context_.set_cipher_list(SSL_CIPHERS)
					
			port_ = int(addressparts_[1])
	
			if (sslcontext_ != None):
				self.factory_.contextFactory = sslcontext_
				reactor.listenSSL(port_, self.factory_, sslcontext_)
			
			else:
				reactor.listenTCP(port_, self.factory_)
					
			Thread(target=reactor.run, args=(False,)).start()
				
		except Exception as inst:
			self.logException(inst)

