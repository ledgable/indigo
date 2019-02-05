
import json

from config import *
from modules import *
from controllers import *

class BaseApplication(BaseClass, metaclass=Singleton):
	
	appInstance_ = None
	configctrl_ = None
	
	# configuration directories ...
	
	@property
	def configctrl(self):
		
		application_ = ApplicationManager(self).get("config")
		return application_
	
	
	@property
	def appInstance(self):
		return self.appInstance_
	

	@property
	def deviceid(self):
		return self.appInstance_.deviceid
	
	
	@property
	def devicedir(self):
		return self.appInstance.datadir + ("/%s" % self.appInstance.deviceid)
	
	
	@property
	def configdir(self):
		return self.devicedir + "/config"


	def createDirectories(self):
		
		success_ = True
		
		try:
			if (not os.path.exists(self.devicedir)):
				self.log("Device Directory does not exist - creating")
				os.makedirs(self.devicedir)
			
			if (not os.path.exists(self.configdir)):
				self.log("Config Directory does not exist - creating")
				os.makedirs(self.configdir)
	
		except Exception as inst:
			self.logException(inst)
			success_ = False

		return success_
					
					
	def configUpdated(self):

		self.log("Informed that configuration is updated or has loaded!")


	def shutdown(self):

		self.log("Node Shutting down gracefully")


	def __init__(self, appInstance=None):

		# we create a link back to the app for information purposes...
		self.appInstance_ = appInstance

		self.log("Platform detected = %s" % (sys.platform))

		success_ = self.createDirectories()




