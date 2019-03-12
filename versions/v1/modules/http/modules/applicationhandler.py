
from modules.repeater import *
from modules.daoobject import *
from modules.baseclass import *
from modules.singleton import *

class AppHandler(BaseClass, metaclass=Singleton):
	
	handlers_ = None
	
	def poller(self, args):
		pass
	
	
	def forsite(self, sitename):
		
		sitename_ = sitename.lower()
		sites_ = list(self.handlers_.keys())
		
		for site_ in sites_:
			hostnames_ = self.handlers_[site_].CONFIG.HOST_NAMES
			if (hostnames_ != None):
				if (sitename_ in hostnames_):
					return self.handlers_[site_]
					break
	
		if ("default" in sites_):
			return self.handlers_["default"]

		return None
	
	
	@property
	def sites(self):
		return self.handlers_
	
	
	def addsite(self, sitename=None, handler=None):
		if (handler != None):
			self.handlers_[sitename] = handler


	def __init__(self):
		
		self.handlers_ = {}
		timer = Repeater(30.0, self.poller, self)
		timer.start()
		
		self.log("Created instance of apphandler singleton")



class ApplicationHandler(BaseClass):

	site_ = None
	directory_ = None
	sessions_ = None
	resources_ = None
	controllers_ = None
	config_ = None
	authentication_ = None

	def poller(self, args):
		pass

	@property
	def CONFIG(self):
		return self.config_

	@property
	def SITE(self):
		return self.site_

	@property
	def AUTHENTICATION(self):
		return self.authentication_

	@property
	def CONTROLLERS(self):
		return self.controllers_

	@property
	def SESSIONS(self):
		return self.sessions_

	@property
	def RESOURCES(self):
		return self.resources_

	def __init__(self):

		self.config_ = DAOObject({})
		
		self.timer_ = Repeater(10.0, self.poller, self)
		self.timer_.start()

		self.log("Created instance of apphandler")


