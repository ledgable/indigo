
from modules.http.modules import *

PARSER = Parser()

class Controller(HTTPController):

	def __init__(self, handler, session, query=None, isajax=False):
		self.session = session
		self.handler = handler
		self.isajax = isajax
	
	@property
	def secure(self):
		return RawVars().secure
	
	@property
	def ipaddress(self):
		return self.handler.ipaddress
	
	def base64decode(self, data):
		if len(data):
			data += '=' * (4 - len(data) % 4)
		return base64.b64decode(data)
	
	def defaultVal(self, dictinfo, key, default):
		if dictinfo != None:
			if key in dictinfo.keys():
				return dictinfo[key]
		return default
	
	# string.ascii_uppercase + string.digits
	def randomCode(self, size=4, chars=string.digits):
		return ''.join(random.choice(chars) for _ in range(size))
	
	@property
	def baseFileRef(self):
		ROOT = os.path.dirname(os.path.abspath(__file__)) + "/../"
		return ROOT + self.handler.DIRECTORY
	
	def dateToEpoch(self, date):
		
		tz_ = self.session.timezone
		datelocal_ = datetime.datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
		localdt_ = tz_.localize(datelocal_)
		utcdt_ = localdt_.astimezone(pytz.utc)
		epoch_ = int(utcdt_.timestamp())
		
		return epoch_
	
	def curr(self, value=0.0, dps=2):
		return self.number(value, dps)
	
	def number(self, value=0.0, decimals=0):
		return ("{0:,."+str(decimals)+"f}").format(float(value))
	
	def loadContent(self, filename=None, appVars=None, root="views"):
		return PARSER.loadContent(self, filename, appVars, root)

	def appendView(self, viewName=None, content=None, appVars=None):
		return PARSER.appendView(self, viewName, content, appVars)


	
