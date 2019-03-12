
from www.__common.controllers.NodeController import *

class DefaultController(NodeController):

	def __init__(self, handler, session, query=None, isajax=False):		
		NodeController.__init__(self, handler, session, query, isajax)
	
	
	@endpoint(97, True, False, None, "get", "^/.serviceid", "Get service identifier")
	def getServiceId(self, postData=None, appVars=None):
		
		out_ = self.handler.server.manager.deviceid_
		bytes_ = out_.encode(UTF8)
		
		return FunctionResponse(HTTP_OK, "application/txt",  bytes_)
	
	
	@endpoint(97, True, False, None, "get", "^/.htaccess", "Get htaccess")
	def getHtAccess(self, postData=None, appVars=None):

		out_ = """Header add Access-Control-Allow-Origin '*'"""
		bytes_ = out_.encode(UTF8)
		
		return FunctionResponse(HTTP_OK, "application/txt",  bytes_)
	
	
	@endpoint(1, True, True, None, "get", "^/robots.txt", "Get robots file")
	def robots(self, postData=None, appVars=None):
		
		servicename_ = self.handler.CONFIG.SERVICE_NAME
		
		newContent_ = """User-agent: *\r\n"""
		newContent_ += """Disallow: /cgi-bin/\r\n"""
		newContent_ += """Disallow: /tmp/\r\n"""
		
		return FunctionResponse(HTTP_OK, TYPE_HTML, newContent_)
	
	
	@endpoint(98, True, False, None, "get", "(?P<filename>/(js|favicon|images|css)/[^ ]*)", "Get File")
	def file(self, postData=None, appVars=None, filename=None, directory="files"):

		newContent_ = None
		modified_ = None
		compressed_ = None
		
		if (filename != None):

			fileExtension_ = None
			size_ = 0
			
			try:
				extension_ = os.path.splitext(filename)[1][1:]

				if (extension_ != None):
					fileExtension_ = extension_.lower()
				
				newContent_, compressed_, modified_, size_ = self.handler.RESOURCES.resourceForUrl(("%s/%s" % (directory, filename)), True)
		
			except Exception as inst:
				self.logException(inst)
			
			response_ = None
			
			if (compressed_ != None) and (appVars.allowcompression):
				response_ = FunctionResponse(HTTP_OK, fileExtension_, compressed_)
				response_.compressed = True
			else:
				response_ = FunctionResponse(HTTP_OK, fileExtension_, newContent_)

			response_.lastmodified = modified_
			response_.size = size_

			return response_

	
	@endpoint(1, True, True, None, "get", "^/favicon.ico", "Get webicon")
	def favIcon(self, postData=None, appVars=None):
		return self.file(postData, appVars, "favicon.ico", "files")

							
	@endpoint(1, True, True, None, "get", "^/api/info/(?P<search>[0-9a-z][^-&*/\%]*)", "Get API Function info")
	def apiInfo(self, postData=None, appVars=None, search=None):
	
		out_ = []
		
		definitions_ = self.handler.CONTROLLERS.routes.all
		
		if definitions_ != None:
			for definition_ in definitions_:
				
				if (definition_.hidden_ == 0):
					controller_ = definition_.controller_
					attrs_ = definition_.sortedAttrs
					newdef_ = {"verb":definition_.method, "uid":definition_.function, "description":definition_.description, "regx":definition_.niceregx, "attrs":attrs_, "controller":controller_}

					if (search == "all") or (search in controller_.lower() or search in newdef_["uid"] or search in newdef_["description"] or search in newdef_["attrs"]):
						out_.append(newdef_)
				
		return FunctionResponse(HTTP_OK, TYPE_JSON, out_)
	
