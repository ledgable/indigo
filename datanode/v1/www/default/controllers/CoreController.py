
from modules.http.controllers.DefaultController import *

class CoreController(DefaultController):
	
	
	def __init__(self, handler, session, query=None, isajax=False):
		DefaultController.__init__(self, handler, session, query, isajax)

	
	@endpoint(1, True, True, None, "get", "^/__ping", "Get session info")
	def ping(self, postData=None, appVars=None, messageTop=-1):
		
		username_ = self.session.username
		result_ = 0

		if (username_ != None):
			result_ = 1

		return FunctionResponse(HTTP_OK, TYPE_JSON, {"loggedin":result_})


	@endpoint(99, True, True, None, "get", "(?P<pagename>/[^ ]*)", "Fetch page by name")
	def page(self, postData=None, appVars=None, pagename=None):
		
		if (pagename != None):
			if (pagename[0:1:] == "/"):
				pagename = pagename[1:]
		
		if (pagename == None) or (pagename == ""):
			pagename = "default"
	
		content_ = self.loadContent(("main/%s.html.py" % pagename), appVars)
		
		if (content_ == None):
			return FunctionResponse(HTTP_PAGE_DOES_NOT_EXIST, None, None)

		contentout_ = content_
	
		if self.isajax == False:
			contentout_ = self.appendView("template_web.html", content_, appVars)
		
		return FunctionResponse(HTTP_OK, TYPE_HTML, contentout_)
