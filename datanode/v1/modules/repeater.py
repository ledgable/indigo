
import threading
import string, cgi, time

from time import sleep
from threading import Timer
from threading import Thread

class Repeater(Thread):
	
	running_ = False
	lastpoll_ = None
	
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
		self.interval=interval
		self.action=action
		self.args=args
		self.running_=True
	
	def run(self):
		
		if (self.action == None):
			return
				
		while (self.running_):
			sleep(self.interval)
			
			if (self.running_):
				t = threading.Thread(target=self.action, args=[self.args])
				t.daemon = True
				t.start()

	def stop(self):
		
		self.running_=False
