
from modules.daoobject import *
from modules.baseclass import *
from modules.singleton import *


class ApplicationManager(BaseClass, metaclass=Singleton):

	appInstance_ = None
	applications_ = None
		
	def start(self, key, application):
	
		if (key != None) and (application != None):
			
			self.applications_[key] = application
			self.log("Starting application instance %s" % key)


	def get(self, key):
		
		if (key != None):
			if (key in self.applications_.keys()):
				return self.applications_[key]
			
		return None


	@property
	def appInstance(self):
		
		return self.appInstance_


	def __init__(self, appInstance=None):

		self.applications_ = {}
		self.appInstance_ = appInstance

		self.log("Created instance of application manager")


	def shutdown(self):

		self.log("Shutdown received")

		keys_ = list(self.applications_.keys())
			
		for key_ in keys_:
			application_ = self.applications_[key_]
			application_.shutdown()
			del self.applications_[key_]
			self.log("Shutdown completed for application %s" % key_)
