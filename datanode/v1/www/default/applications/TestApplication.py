
from modules.daoobject import *

from modules.http.modules.controllermanager import *

class TestApplication(HTTPApplication):

	@property
	def chains(self):
	
		configctrl_ = self.handler.cnc.configctrl
		
		if (configctrl_ != None):
			return configctrl_.chains
		
		return None


	def poller(self, args):
	
		pass


	def __init__(self, manager):
		
		HTTPApplication.__init__(self, manager)
		
		self.log("This is a test application that runs in the background - you can customize this quite easily!")

		self.timer_ = Repeater(60.0, self.poller, self)
		self.timer_.start()



	
