
import threading
import string, cgi, time

from time import sleep
from threading import Timer
from threading import Thread

class Repeater(Thread):
	
	running_ = False
	lastpoll_ = None
	interval_ = 0
	action_ = None
	args_ = None
	
	@property
	def running(self):
		
		return self.running_

	
	@property
	def lastpoll(self):
		
		return self.lastpoll_

	
	def __init__(self, interval, action, args):
		
		Thread.__init__(self)
		self.running_ = False
		self.lastpoll_ = 0
		self.interval_ = interval
		self.action_ = action
		self.args_ = args
		self.running_ = True

	
	def run(self):
		
		if (self.action_ == None):
			return
				
		while (self.running_):
			sleep(self.interval_)
			
			if (self.running_):
				t = threading.Thread(target=self.action_, args=[self.args_])
				t.daemon = True
				t.start()


	def stop(self):
		
		self.running_ = False
