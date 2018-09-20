
from .server import *
from .modules import *

class HttpManager(BaseClass):

	servers_ = None
	manager_ = None
	listening_ = False
	
	@property
	def servers(self):
		return self.servers_
	
	
	def serve_forever(self):
		
		while self.listening_:
			readers_, writers_, exceptions_ = select.select(self.servers, [],[])
			for server_ in readers_:
				server_._handle_request_noblock()


	def __init__(self, manager=None, httpPorts=0):
		
		self.servers_ = []
		self.manager_ = manager
		self.listening_ = True
		
		class PoolHTTPServer(AppServer, HTTPServer):
			pass
		
		# Load Mimetypes
		
		directory_ = os.path.dirname(os.path.abspath(__file__ + "/../../"))
			
		with open(("%s/config/mimetypes.supported" % (directory_)), 'r', encoding=UTF8) as fileConfig:
			for line in fileConfig:
				parts = line.split(",")
				if (len(parts) == 2):
					mimeinfo_ = parts[1]
					if mimeinfo_[-1::] == "\n":
						mimeinfo_ = mimeinfo_[:-1:]
					MIMETYPES[parts[0]] = mimeinfo_
		
		self.sites_ = SiteLoader(manager)
			
		if len(AppHandler().sites) == 0:
			print('Error - No sites found')
			os._exit(0)

		for port_ in httpPorts:
			server_ = PoolHTTPServer((HTTP_LISTENON, (port_)), ApplicationHandler, bind_and_activate=False)
			server_.instanceid = port_
			server_.manager_ = manager
			server_.server_bind(port_)
			server_.server_activate()
			self.servers_.append(server_)
			
		Thread(target=self.serve_forever, args=()).start()
