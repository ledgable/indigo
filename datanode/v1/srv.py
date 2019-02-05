
import os

from signal import *

from config import *
from modules import *
from controllers import *
from applications import *

IPBLOCKER = IPBlocker()

class MainApp(BaseClass):
	
	root_ = os.path.dirname(os.path.abspath(__file__)) + "/./"
	listening_ = False
	
	listenon_ = "0.0.0.0:9996"
	server_ = "indexer.ledgable.com:9908"
	
	applications_ = None	
	deviceid_ = None
	devicepin_ = None
	httpserver_ = None
	httpports_ = None
	datadir_ = None
	register_ = None
	
	@property
	def datadir(self):
		return self.datadir_
	
	@property
	def root(self):
		return self.root_
	
	@property
	def register(self):
		if (self.register_ != None):
			return self.register_
		else:
			return "0.0.0.0"
	
	@property
	def listenon(self):
		return self.listenon_
	
	@property
	def devicedir(self):
		return self.datadir + ("/%s" % self.deviceid)
	
	@property
	def configdir(self):
		return self.devicedir + "/config"
	
	@property
	def deviceid(self):
		return self.deviceid_
	
	@property
	def devicepin(self):
		return self.devicepin_
	
	@property
	def server(self):
		return self.server_
	
	@property
	def applications(self):
		return self.applications_
	
	def shutdown(self, reason="No Reason"):
		
		self.log("Shutdown invoked | Reason = \033[31m%s\033[0m" % (reason))
		self.listening_ = False
		
		if (self.applications_ != None):
			self.applications_.shutdown()
		
		self.log("Shutdown completed")
		sys.exit(0)

	def __init__(self, argv):
		
		# lets start the show...
		
		self.httpports_ = None
		self.listening_ = True
		
		def signal_handler(*args):
			try:
				self.shutdown("App terminated due to signal")
			
			except SystemExit:
				os._exit(0)
	
		for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
			signal(sig, signal_handler)

		try:
			opts, args = getopt.getopt(argv,"hl:d:p:s:o:r:",["help","listen=","deviceid=","pin=","server=","httpport=","register=", "debug"])
		
		except getopt.GetoptError as e:
			self.log("Issue with arguments - quitting")
			self.log("Try 'srv.py -h' for help")
			os._exit(0)

		for opt, arg in opts:
			if opt == "-h":
				self.listenon_ = None
			elif opt in ("-d", "--deviceid"):
				self.deviceid_ = arg.lower()
			elif opt in ("-o", "--httpport"):
				self.httpports_ = map(int, arg.split(","))
			elif opt in ("-p", "--pin"):
				self.devicepin_ = arg
			elif opt in ("-l", "--listen"):
				self.listenon_ = arg
			elif opt in ("-r", "--register"):
				self.register_ = arg
			elif opt in ("-s", "--server"):
				self.server_ = arg
			elif opt in ("--debug"):
				RawVars().debug_ = True

		if (self.listenon_ == None):
			
			url_ = self.root_ + "/text/readme_en.txt"
			
			content_ = ""
			
			with open(url_, 'r', encoding=UTF8) as fileRead:
				content_ = fileRead.read()
			
			for textcontent_ in content_.split("\n"):
				self.out(textcontent_)
			
			os._exit(0)

		else:
			
			self.log("Current directory = %s" % (self.root_))

			# the main data directory !!
			self.datadir_ = self.root_ + "__data"
			
			if (not os.path.exists(self.datadir_)):
				self.log("Data Directory does not exist - creating")
				os.makedirs(self.datadir_)
		
			devicesfound_ = os.listdir(self.datadir_)

			if (self.deviceid_ == None):
				
				if (len(devicesfound_) == 0):
					self.log("No deviceid - goto https://ledgable.com to create one")
					os._exit(0)

				elif (len(devicesfound_) == 1):
					self.deviceid_ = devicesfound_[0]
					if (self.devicepin_ != None):
						self.log("Found device configuration = %s" % (self.deviceid_))
					
					else:
						self.log("Missing pin code - Quitting")
						os._exit(0)
				
				else:
					self.log("Cannot determine deviceid - there are multiple devices registered at this instance (%s)" % (devicesfound_))
					os._exit(0)

			else:
				
				if (self.devicepin_ != None):
					if (self.deviceid_ in devicesfound_):
						self.log("Found device configuration = %s" % (self.deviceid_))
					
					else:
						self.log("Assigning deviceid = %s" % (self.deviceid_))

				else:
					self.log("Missing pin code - Quitting")
					os._exit(0)

			if (self.httpports_ != None):
				self.httpserver_ = HttpManager(self, self.httpports_)

			configmanager_ = ConfigController(self, self.server)
			configmanager_.start()
			
			self.applications_ = ApplicationManager(self)
			
			ApplicationManager(self).start("config", configmanager_)
			ApplicationManager(self).start("datanode", DataNodeApplication(self))


def main(argv):
	app = MainApp(argv)

if __name__ == '__main__':
	main(sys.argv[1:])

