
import importlib.util
import os
import json

from modules.baseclass import *
from modules.singleton import *

from modules.http import *
from modules.http.modules import *

class SiteLoader(BaseClass, metaclass=Singleton):

	manager_ = None
	directory_ = None
	
	@property
	def manager(self):
		return self.manager_
	
	def __init__(self, manager):
		
		self.manager_ = manager
		self.directory_ = os.path.dirname(os.path.abspath(__file__ + "/../../../../") + "/www/")
		
		self.log("Created instance of siteloader singleton")
		self.loadSites()

	def loadSites(self):

		out_ = []
		
		for sitedir_ in os.listdir(self.directory_):

			if (sitedir_[0:1] != "."):
				if (sitedir_[0:2] != "__"):
					
					out_.append(sitedir_)
					path_ = self.directory_ + "/" + sitedir_
					
					try:
						
						siteroot_ = path_
						configfileurl_ = path_ + "/config/appconfig.json"
						
						jsondata_ = open(configfileurl_).read()
						configraw_ = json.loads(jsondata_)
						config_ = DAOObject(configraw_)
						
						if (config_.enabled == None) or (config_.enabled == 1):
							
							self.log("Loading site %s" % sitedir_)

							appHandler_ = ApplicationHandler()
							
							setattrs(appHandler_,
									site_ = sitedir_,
									directory_ = ("/www/" + sitedir_),
									config_ = config_,
									sessions_ = SessionMgr(),
									authentication_ = SecurityMgr(path_),
									resources_ = ResourceMgr(path_),
									controllers_ = ControllerManager(self.manager_)
									)
							
							AppHandler().addsite(sitedir_, appHandler_)
							
							appHandler_.controllers_.loadControllerGroup(self.directory_ + "/__common/controllers")
							appHandler_.controllers_.loadControllerGroup(path_ + "/controllers")
							appHandler_.controllers_.loadControllerGroup(path_ + "/applications")

					except Exception as inst:
						self.logException(inst)

		return out_

