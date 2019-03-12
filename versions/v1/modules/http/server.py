
import re
import os
import glob
import hashlib
import uuid
import urllib
import socket
import select
import socketserver
import concurrent.futures
import zlib

import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import base64
import errno
import http.client

from OpenSSL import SSL

import sys, getopt, imp, traceback

from pytz import timezone

from io import StringIO
from xml.dom.minidom import Document
from decimal import Decimal

from signal import *
from netifaces import AF_INET, AF_INET6, AF_LINK
from ssl import SSLError

import netifaces as ni

from netaddr import IPNetwork, IPAddress

from socketserver import ForkingMixIn, ThreadingMixIn
from concurrent.futures import ThreadPoolExecutor

from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie as cookie

from os import curdir, sep
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from http import cookies

from twisted.internet import reactor
from twisted.internet import ssl as tSSL

from threading import Timer, Thread
from time import sleep

from modules import *
from dataobjects import *

from .modules.applicationhandler import *
from .modules.coreserver import *

MIMETYPES = {}
SESSIONPARSER = re.compile("^(([0-9a-f]){32})$", re.IGNORECASE | re.VERBOSE | re.DOTALL)

#####################################
####
####  Connection Handler
####
#####################################

class AppServer(CoreServer):
	
	manager_ = None
	
	@property
	def manager(self):
		return self.manager_
	
	def finish_request(self, request, client_address, country_code, isssl):
		MyHandler(request, client_address, self, country_code, isssl)


class MyHandler(CoreHandler):
	
	interfaces = None
	mimeTypes = None
	apphandler = None


	def __init__(self, request, client_address, server, country_code, isssl=False):
		CoreHandler.__init__(self, request, client_address, server, country_code, isssl)


	@property
	def CONFIG(self):
		return self.apphandler.config_


	@property
	def SITE(self):
		if (self.apphandler != None):
			return self.apphandler.site_

		return "UNDEFINED"


	@property
	def LOCALE(self):
		return self.apphandler.locale_


	@property
	def SESSIONS(self):
		return self.apphandler.sessions_


	@property
	def CONTROLLERS(self):
		return self.apphandler.controllers_


	@property
	def AUTHENTICATION(self):
		return self.apphandler.authentication_


	@property
	def DIRECTORY(self):
		return self.apphandler.directory_


	@property
	def RESOURCES(self):
		return self.apphandler.resources_


	@property
	def error_message_format(self):
		return '<body><h1>Error %(code)d</h1><p>%(message)s / %(explain)s</p></body>'


	@property
	def server_version(self):
		return SERVICE_VERSION


	@property
	def sys_version(self):
		return SERVER_NAME


	def reformat(self, data=None, format="html"):
		
		if (format == TYPE_JSON):
		
			from modules.customencoder import CustomEncoder
			
			if (data == None):
				return None
				
			elif issubclass(data.__class__, extlist):
				return json.dumps(data.all, cls=CustomEncoder)
			
			elif issubclass(data.__class__, extdict):
				return json.dumps(data.dict(), cls=CustomEncoder)
			
			elif type(data) == type(dict()):
				return json.dumps(data, cls=CustomEncoder)
			
			elif type(data) == type(list()):
				return json.dumps(data, cls=CustomEncoder);
			
			else:
				return str(data, UTF8)
		
		elif (format == TYPE_XML):
			dictOut = {'root':data}
			xml = dict2xml(dictOut)
			return xml.display + NEW_LINE

		elif (format == TYPE_XMLS):
			pass

		return data


	def parseAcceptLanguage(self, acceptLanguage):
		
		languages = acceptLanguage.split(",")
		locale_q_pairs = []

		for language in languages:
			split_ = language.split(";")
			
			if (len(split_) > 0):
				if (split_[0] == language):
					# no q => q = 1
					locale_q_pairs.append((language.strip(), "1"))
				
				else:
					locale = split_[0].strip()
					
					if (len(split_[1].split("=")) > 1):
						q = split_[1].split("=")[1]
						locale_q_pairs.append((locale, q))
					
					else:
						locale_q_pairs.append((locale, "1"))

		return locale_q_pairs


	def detectLocale(self, acceptLanguage):
		
		defaultLocale = "en"
		locale_q_pairs = self.parseAcceptLanguage(acceptLanguage)
		
		for pair in locale_q_pairs:
			for locale in self.CONFIG.SUPPORTED_LANGS:
				# pair[0] is locale, pair[1] is q value
				if pair[0].replace('-', '_').lower().startswith(locale.lower()):
					return locale

		return defaultLocale


	def connection_dropped(self, error, environ=None):
		
		try:
			if self.transactionid_ != None:
				self.log(("connection dropped with error %s" % error))

		except Exception as inst:
			self.logException(inst)


	def parse_request(self):
		"""Parse a request (internal).

		The request should be stored in self.raw_requestline; the results
		are in self.command, self.path, self.request_version and
		self.headers.

		Return True for success, False for failure; on failure, an
		error is sent back.

		"""
		
		self.command = None  # set in case of error on the first line
		self.request_version = version = self.default_request_version
		self.close_connection = True
		
		requestline = str(self.raw_requestline, 'iso-8859-1')
		requestline = requestline.rstrip('\r\n')
		
		self.requestline = requestline
		words = requestline.split()
		
		if (len(words) == 3):
			
			command, path, version = words
			
			try:
				if (version[:5] != 'HTTP/'):
					raise ValueError

				base_version_number = version.split('/', 1)[1]
				version_number = base_version_number.split(".")

				# RFC 2145 section 3.1 says there can be only one "." and
				#   - major and minor numbers MUST be treated as
				#      separate integers;
				#   - HTTP/2.4 is a lower version than HTTP/2.13, which in
				#      turn is lower than HTTP/12.3;
				#   - Leading zeros MUST be ignored by recipients.

				if (len(version_number) != 2):
					raise ValueError
						
				version_number = int(version_number[0]), int(version_number[1])
					
			except (ValueError, IndexError):
				self.send_error(HTTPStatus.BAD_REQUEST, "Bad request version (%r)" % version)
				return False
			
			if (version_number >= (1, 1)) and (self.protocol_version >= "HTTP/1.1"):
				self.close_connection = False

			if (version_number >= (2, 0)):
				self.send_error(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED, "Invalid HTTP version (%s)" % base_version_number)
				return False

		elif (len(words) == 2):
			command, path = words
			self.close_connection = True
			if command != 'GET':
				self.send_error(HTTPStatus.BAD_REQUEST, "Bad HTTP/0.9 request type (%r)" % command)
				return False
			
		elif (not words):
			return False
		
		else:
			command, path, version  = "GET", "", (1,1)

		self.command, self.path, self.request_version = command, path, version

		# Examine the headers and look for a Connection directive.
		try:
			self.headers = http.client.parse_headers(self.rfile, _class=self.MessageClass)
				
		except http.client.LineTooLong as err:
			self.send_error(HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, "Line too long", str(err))
			return False

		except http.client.HTTPException as err:
			self.send_error(HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, "Too many headers", str(err))
			return False

		conntype = self.headers.get('Connection', "")
		
		if (conntype.lower() == 'close'):
			self.close_connection = True

		elif (conntype.lower() == 'keep-alive' and self.protocol_version >= "HTTP/1.1"):
			self.close_connection = False

		# Examine the headers and look for an Expect directive
		expect = self.headers.get('Expect', "")

		if (expect.lower() == "100-continue" and self.protocol_version >= "HTTP/1.1" and self.request_version >= "HTTP/1.1"):
			if not self.handle_expect_100():
				return False
		return True


	def handle_one_request(self):
		
		self.close_connection = 1
		self.server.addRequestWithTransaction(self)
		self.raw_requestline = None
		
		error_ = False

		if (self.rfile.closed):
			self.log(("The channel to read is closed"), "warn")
			self.close_connection = 1
			return
		
		else:
			self.requestline = ''
			self.request_version = ''
			self.command = ''
			
			try:
				self.raw_requestline = self.rfile.readline(65537)
			
			except socket.timeout as e:
				# A read or a write timed out.  Discard this connection
				self.raw_requestline = None
				self.close_connection = 1

			except socket.error as e:
				# Connection reset errors happen all the time due to the browser closing
				# without terminating the connection properly.  They can be safely
				# ignored.
				if (e.errno == errno.ECONNRESET):
					self.raw_requestline = None
					self.close_connection = 1

			except Exception as e:
				self.logException(inst)
				self.raw_requestline = None
				self.close_connection = 1
		
			try:
				if not self.raw_requestline:
					pass
			
				elif self.raw_requestline != b'':
		
					if (len(self.raw_requestline) > 65536):
						# check that the length is not over the top...
						self.log(("Closing connection - data length > 65536"), "warn")
						
						if (not self.wfile.closed):
							self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)

					elif (not self.parse_request()):
							
						if (not self.wfile.closed):
							self.send_error(400)
									
					else:
						host_ = self.headers.get("HOST")
						
						if (host_ == None):
							self.close_connection = 1
							return

						else:
							
							self.apphandler = AppHandler().forsite(host_)							
							
							if (self.apphandler != None):
							
								if (not self.useSSL) and self.CONFIG.REQUIRE_SSL:
								
									new_path = ('https://%s' % (host_))
									self.log(("Redirecting service to %s" % new_path), "info")

									if (not self.wfile.closed):
										self.send_response(HTTP_REDIRECT)
										self.send_header('Location', new_path)
										self.send_header("Content-Length", "0")
										self.end_headers()
						
								else:
									if (self.wfile.closed):
										return # connection is closed - weird...

									else:
										command_ = self.command.lower()
										
										if (command_ in HTTP_ACTIONS.keys()):
											self.close_connection = 0
											self.do_ACTION(HTTP_ACTIONS[command_], host_)

										else:
											self.send_error(HTTPStatus.NOT_IMPLEMENTED)
													
							else:
								self.send_error(HTTPStatus.NOT_IMPLEMENTED)

			# deal with exception issues here...
			
			except SSLError as e:
				if (hasattr(self, 'url')):
					# Happens after the tunnel is established
					self.log(("%s while operating on established SSL tunnel for [%s]" % (e, self.url)), "ssl-critical")
				
				elif (hasattr(self, 'path')):
					self.log(("%s while trying to establish SSL tunnel for [%s]" % (e, self.path)), "ssl-critical")
				
				else:
					self.log(("%s while trying to establish SSL tunnel" % (e)), "ssl-critical")
				
				self.close_connection = 1

			except (FileNotFoundError, BrokenPipeError, ConnectionError, ConnectionResetError, ConnectionResetError) as e:
				self.close_connection = 1

			except (socket.timeout, socket.error, ValueError) as e:
				self.close_connection = 1

			except Exception as inst:
				self.logException(inst)
				self.close_connection = 1

		if (self.close_connection == 1):
			self.finish()

		else:
			if not self.wfile.closed:
				self.wfile.flush()
	
	# clean up and exit here..


	def finish(self):

		if not self.wfile.closed:
			try:
				self.wfile.flush()
			except socket.error:
				# A final socket error may have occurred here, such as
				# the local error ECONNABORTED.
				pass
	
		self.wfile.close()
		self.rfile.close()

		if (self.transactionid_ != None):
			self.server.removeRequestWithTransaction(self.transactionid_)

		self.server.shutdown_request(self.request)


	def do_ACTION(self, action, hostname=None):
		
		vars_ = DAOObject()
		
		setattrs(vars_,
			scheme = HTTP,
			time = time.time(),
			path = urlparse(self.path),
			ipaddress = self.ipaddress,
			browser = "unknown",
			country_code = self.country_code,
			session_id = None,
			device_id = None,
			isajax = False,
			language = "en",
			allowcompression = False
			)

		exitcode_ = HTTP_OK

		if self.useSSL:
			vars_.scheme = HTTPS

		self.transvars = DAOObject()

		# process appvars

		if (vars_.path.query != None) and (vars_.path.query != ""):
			
			splititems_ = vars_.path.query.split("&")
	
			if (len(splititems_) > 0):
		
				for splititem_ in splititems_:
					parts_ = splititem_.split("=")
			
					if (len(parts_) > 1):
						if (parts_[0] in ["format", "position", "pretty"]):
						
							if (parts_[0] == "format"):
								vars_.output = parts_[1]

							elif (parts_[0] == "position"):
								vars_.positionid = parts_[1]
							
							elif (parts_[0] == "pretty"):
								vars_.pretty = parts_[1]

						else:
							vars_.__setattr__(parts_[0], parts_[1])
							
		try:
			headerKeys_ = self.headers.keys()

			for key_ in headerKeys_:
				vars_.__setattr__(key_, self.headers.get(key_))
			
			# If the service is not using SSL, then perform a HTTP redirect to the SSL side...
			
			if (vars_.session_id == "null"):
				vars_.session_id = None
			
			if (vars_.device_id == None) or (vars_.device_id == "null"):
				vars_.device_id = self.uniqueId
			
			# check encoding allows for compression
			
			if (vars_.AcceptEncoding != None):
				encodingoptions_ = vars_.AcceptEncoding.split(",")
				for option_ in encodingoptions_:
					if option_[0:1:] == " ":
						option_ = option_[1:].lower()
				if "deflate" in option_:
					vars_.allowcompression = True
			
			# check some headers of course (page headers of course)
			
			if (vars_.AcceptLanguage != None):
				vars_.language = self.detectLocale(vars_.AcceptLanguage)
			
			# recover session etc. information if available from cookie !!

			if (vars_.session_id == None):
				cookiestring_ = "\n".join(self.headers.get_all('Cookie',failobj=[]))
				cookiein_ = cookie()
				cookiein_.load(cookiestring_)
				
				for m_ in cookiein_:
					if (m_ in COOKYMAP.keys()):
						vars_.__setattr__(COOKYMAP[m_], cookiein_[m_].value)
			
			# is this an ajax call?
			
			if (vars_.http_x_requested_with == AJAX_TOKEN) or (vars_.xrequestedwith == AJAX_TOKEN):
				referer = vars_.referer
			
				if (referer != None) and (self.CONFIG.CROSS_CHECK != None):
					if (referer.lower().find(self.CONFIG.CROSS_CHECK)) != -1:
						vars_.isajax = True
					
					else:
						self.log(("Attempt to cross-script access from the service.. %s " % referer))
						self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
						self.close_connection = 1
						return

				else:
					vars_.isajax = True
		
			# check useragent for allowing access...
			
			if (vars_.useragent != None):
				vars_.useragent = vars_.useragent.lower()
				
				for agent_ in AUTOBLOCK_USERAGENTS:
					if (vars_.useragent.find(agent_) != -1):
						self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
						self.close_connection = 1
						return
				
				for agent_ in ALLOWED_USERAGENTS:
					if (vars_.useragent.find(agent_) != -1):
						vars_.browser = agent_
						break
	
		except Exception as inst:
			self.logException(inst)
			self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
			self.close_connection = 1
			return
				
		routefound_ = None
		
		if (action in [HTTP_ACTION_GATEWAY]):
			
			if (vars_.contentlength != None):
				
				length_ = int(vars_.contentlength)
				
				if (length_ > 0):
					
					postData_ = self.rfile.read(length_)
					encoded_ = postData_.decode(UTF8)
					dict_ = json.loads(encoded_)
					
					if (dict_ != None) and ("actions" in dict_.keys()):
						
						actionsFound_ = dict_["actions"]
												
						if (len(actionsFound_) == 1):
							
							gatewayAction_ = actionsFound_[0]
							
							action_ = gatewayAction_["action"]
							content_ = None
							params_ = DAOObject(gatewayAction_["data"])
							
							if ("content" in gatewayAction_.keys()):
								content_ = gatewayAction_["content"]
						
							routefound_ = self.CONTROLLERS.routes.match(action_, HTTP_ACTION_GATEWAY)
							
							if (routefound_ != None):
								if (routefound_.vars_ == None):
									routefound_.vars_ = {}
								
								routefound_.vars_.update({"params":params_, "content":content_})

		else:
			routefound_ = self.CONTROLLERS.routes.match(vars_.path.path, action)
		
		if (routefound_ == None):
			self.log(("Route invalid - %s:%s" % (action, vars_.path.path)))

		else:
			permissionsreq_ = routefound_.auth # get extended information (like permissions and user info etc)
			session_ = None	# do session binding !!
			
			if (not routefound_.tracksession):
				
				vars_.session_id = NO_TRACK
				session_ = self.SESSIONS.noTrackSession
				
				if (permissionsreq_ != None):
					self.log(("cannot execute permission check on a non-authenticated connection"), "warn")
					self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
					self.close_connection = 1
					return
			
			else:
								
				if (vars_.session_id != None):
					
					current_ = re.findall(SESSIONPARSER, vars_.session_id);
					
					if (len(current_) > 0):
						session_ = self.SESSIONS.sessionForId(vars_.session_id)
					
						if (session_ == None):
							vars_.session_id = None # reset session with a new one !
									
					else:
						self.log(("Spoofing sessionid - %s" % (vars_.session_id)), "session")
						self.close_connection = 1
						return
					
					if (session_ != None) and (session_.id_session == None):
						vars_.session_id = None

				if (vars_.session_id == None):
					session_ = self.SESSIONS.newSession(self.ipaddress, vars_.language, vars_.browser, vars_.useragent, self.country_code)
					vars_.session_id = session_.id_session

				if (session_.lang == None):
					session_.lang = vars_.language

				# Authenticate the connection (if not done already)

				if (session_.username == None):
					if (vars_.authorization != None):
						
						realm_, success_, username_, password_, permissions_ = self.AUTHENTICATION.check(vars_.authorization)
			
						if (realm_ == "basic"):
							if (success_):
								session_.username = username_
								session_.permissions = permissions_
							else:
								self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
								self.close_connection = 1
								return
						
						else:
							vars_.authentication = {"username":username_, "password":password_, "realm":realm_}

					else:
						if (self.CONFIG.REQUIRE_AUTH == 1):
							if (self.CONFIG.PROMPT_AUTH == 1):
							
								# use the browser default authentication process
								if (vars_.authorization == None):
									self.send_response(HTTP_SESSION_FAILURE)
									self.send_header("WWW-Authenticate", "Basic")
									self.end_headers()
									self.close_connection = 1
									return
						
							self.send_error(HTTP_FORBIDDEN, RESPONSE_ACCESS_DENIED)
							self.close_connection = 1
							return

			# check permission set...

			if (permissionsreq_ != None):
				
				success_ = False
				
				if (session_.permissions != None):
					for permissionreq_ in permissionsreq_:
						if permissionreq_ in session_.permissions:
							success_ = True
							break;
			
				if (not success_):
					self.log(("Method not allowed (%s)" % (routefound_.function)))
					self.send_error(HTTP_METHOD_NOT_ALLOWED, RESPONSE_NO_PERMISSIONS)
					self.close_connection = 1
					return

			# if the connection is invalid return state 400

			if (session_ != None):
				
				controller_ = None
				postData_ = None
				contentout_ = None
				response_ = None
				function_ = None
				format_ = None
				length_ = 0

				try:

					# ignore postdata if the request is a get/delete etc...
					
					if ((routefound_ != None) and (routefound_.controller != None)):

						if (action not in [HTTP_ACTION_GET, HTTP_ACTION_DELETE, HTTP_ACTION_GATEWAY]):
							
							if (vars_.contentlength != None):
								length_ = int(vars_.contentlength)
						
								if (length_ > 0):
									postData_ = self.rfile.read(length_)
						
						module_ = self.CONTROLLERS.controllerForId(routefound_.controller)
												
						if (module_ != None):
							class_ = getattr(module_, routefound_.controller)
							controller_ = class_(self, session_, vars_.path.query, vars_.isajax)
							
							if (routefound_.function):
								function_ = getattr(controller_, routefound_.function)
						
						# no data to post !
						if (function_ != None):
							
							if (routefound_.vars != None) and (len(routefound_.vars) > 0):
								response_ = function_(postData_, vars_, **routefound_.vars)
							else:
								response_ = function_(postData_, vars_)
									
							if (response_ != None):
								exitcode_ = response_.response
								format_ = response_.mimetype
							
							else:
								exitcode_ = HTTP_NO_CONTENT

							if (exitcode_ == HTTP_OK):
								pass
											
							elif (exitcode_ == HTTP_NOT_ACCEPTABLE):
								self.log(("Request failed with reason - %s:%s" % (action, vars_.path.path)))
													
							elif (exitcode_ != HTTP_NO_CONTENT):
								self.log(("Request failed with code %d - %s:%s" % (exitcode_, action, vars_.path.path)))
														
						else:
							self.log(("%s | %s" % (routefound_.function, routefound_.vars)))

				except Exception as inst:
					self.logException(inst)

				finally:
					if (controller_ == None) or (response_ == None):
						exitcode_ = HTTP_PAGE_DOES_NOT_EXIST

				# now render the result

				if (response_ != None):
					
					now_ = time.time()
					expires_ = now_ + 2419200
					sendcontent_ = 1
					compress_ = response_.compressed

					if (exitcode_ in [HTTP_SESSION_FAILURE]):
						
						self.send_response(exitcode_)
						self.send_header("WWW-Authenticate", response_.content)
						self.end_headers()
						self.close_connection = 1						
						return
							
					elif (exitcode_ in [HTTP_OK, HTTP_NOT_ACCEPTABLE]):
						
						contentout_ = self.reformat(response_.content, format_)
						dataout_ = contentout_
						
						if (not response_.isbinary):
							if (dataout_ != None):
								if (format_ in TEXT_TYPES):
									dataout_ = bytes(contentout_, UTF8)
					
						if (dataout_ != None) and (not response_.compressed) and (vars_.allowcompression):
							compress_ = True
							dataout_ = zlib.compress(dataout_)
						
						response_.content = dataout_
						sendcookies_ = False
											
						if (format_ in [TYPE_RAW, TYPE_HTML, TYPE_JSON, TYPE_XMLS, TYPE_XML]):
							
							self.send_response(exitcode_)
							
							if compress_:
								self.send_header("Content-Encoding", "deflate")

							self.send_header("Content-Type", MIMETYPES[format_])

							if (response_.content == None):
								self.send_header("Content-Length", str(0))
							else:
								self.send_header("Content-Length", str(len(response_.content)))
							
							sendcookies_ = True

						elif (format_ != None):
							
							if (response_.lastmodified != None):
								
								if (response_.lastmodified == 0):
									
									self.send_response(HTTP_OK)
									self.send_header("Expires","0")
									self.send_header("Pragma-Directive", "no-cache")
									self.send_header("Cache-Directive", "no-cache")
									self.send_header("Cache-Control", "no-cache")
									
									if compress_:
										self.send_header("Content-Encoding", "deflate")

									if (format_ in MIMETYPES.keys()):
										self.send_header("Content-Type", MIMETYPES[format_])
									else:
										self.send_header("Content-Type", format_)
									
									self.send_header("Pragma", "no-cache")

								else:
									
									modifiedsince_ = None

									if (vars_.ifmodifiedsince != None):
										modifiedsince_ = vars_.ifmodifiedsince
									
									datelastmodified_ = datetime.datetime.strptime(time.ctime(response_.lastmodified), "%a %b %d %H:%M:%S %Y")
									datemodified_ = datelastmodified_.strftime("%a, %d %b %Y %H:%M:%S GMT")
				
									if (datemodified_ == modifiedsince_):
										self.send_response(HTTP_NOT_MODIFIED)
										sendcontent_ = 0
										response_.content = None
										self.send_header("Cache-Control", "max-age=86400, public")
								
									else:
										self.send_response(HTTP_OK)
										
										dateexpires_ = datetime.datetime.strptime(time.ctime(expires_), "%a %b %d %H:%M:%S %Y")
										self.send_header("Expires", dateexpires_.strftime("%a, %d %b %Y %H:%M:%S GMT"))
										self.send_header("Last-Modified", datemodified_)
										self.send_header("Cache-Control", "max-age=86400, public")
										
										if compress_:
											self.send_header("Content-Encoding", "deflate")

										if (format_ in MIMETYPES.keys()):
											self.send_header("Content-Type", MIMETYPES[format_])
										else:
											self.send_header("Content-Type", format_)
										
										self.send_header("Pragma", response_.cachetype)

							else:
								
								self.send_response(HTTP_OK)
								self.send_header("Cache-Control", "max-age=900, must-revalidate")

								if compress_:
									self.send_header("Content-Encoding", "deflate")

								if (format_ in MIMETYPES.keys()):
									self.send_header("Content-Type", MIMETYPES[format_])
								else:
									self.send_header("Content-Type", format_)

								self.send_header("Pragma","private")

							if (response_.content != None) and (sendcontent_ == 1):
								self.send_header("Content-Length", str(len(response_.content)))

						else:
							self.send_response(HTTP_PAGE_DOES_NOT_EXIST)
							self.send_header("Connection", "Close")
							self.end_headers()
							self.close_connection = 1
							return

						if (vars_.session_id != NO_TRACK) and sendcookies_:
							
							# send recovery header for http session handling
							self.send_header("session_id", vars_.session_id)

							# OWASP Compliance

							# prevent TLS issues arising
							self.send_header("Strict-Transport-Security", "max-age=86400; includeSubDomains")
							
							# prevent iframe abuse (only allow same origin) - options are...
							# ALLOW-FROM https://example.com/
							# DENY
							# SAMEORIGIN
							self.send_header("X-Frame-Options", "SAMEORIGIN")

							# prevent Cross Site Scripting etc
							self.send_header("X-XSS-Protection", "1; mode=block")
							self.send_header("X-Content-Type-Options", "nosniff")
							
							# send cookies
							cookies_ = {"session_id": vars_.session_id, "device_id":vars_.device_id, "language":vars_.language}
							expires_ = datetime.datetime.strptime(time.ctime(now_+TIMEOUT), "%a %b %d %H:%M:%S %Y")

							cookie_ = cookie()

							for cookiekey_ in cookies_.keys():
								
								cookie_[cookiekey_] = cookies_[cookiekey_]
								cookie_[cookiekey_]["httponly"] = True
								
								# if we use a default servicename, then cookies should link to the hostname
								
								if (self.CONFIG.SERVICE_NAME == "*"):
									host_ = vars_.HOST
									cookie_[cookiekey_]["domain"] = host_

								else:
									cookie_[cookiekey_]["domain"] = ("." + self.CONFIG.SERVICE_NAME)

								cookie_[cookiekey_]["path"] = "/"
								cookie_[cookiekey_]["max-age"] = TIMEOUT
								cookie_[cookiekey_]["expires"] = expires_
								cookie_[cookiekey_]["secure"] = self.CONFIG.REQUIRE_SSL

								_cookieOut = cookie_[cookiekey_]
								self.send_header('Set-Cookie', _cookieOut.OutputString())

							# send user identifier
							
							if (session_.username != None):
								self.send_header("X-Userid", session_.username)

							# send render time (for page)

							self.send_header("X-Time", ("%s" % (now_ - vars_.time)))

						if (response_.release):
							self.end_headers()
							self.returnResponse(exitcode_, response_.content, True)
						
						else:
							self.send_header("Connection", "Keep-alive")
							self.send_header("Keep-Alive", "max=5, timeout=120")
							self.close_connection = 0

						return
			
		self.send_response(exitcode_)
		self.send_header("Content-Type", "text/html")
		self.send_header("Connection", "Close")
		self.end_headers()
		self.close_connection = 1
			
			
	def returnResponse(self, exitcode, content=None, release=False):
		
		if (exitcode == HTTP_OK):

			try:
				if (content != None):
					if (not self.wfile.closed): # maybe we have a broken pipe at this point....
						while len(content) > PACKET_SIZE:
							fp_ = content[:PACKET_SIZE:]
							content = content[PACKET_SIZE:]
							
							if self.wfile != None:
								self.wfile.write(fp_)
							else:
								break

						if self.wfile != None:
							self.wfile.write(content)

				if release:
					self.close_connection = 1

			except IOError as e:
				self.close_connection = 1
			
			except Exception as inst:
				self.logException(inst)
				self.close_connection = 1


#####################################
####
####  SITE SPECIFIC APP BEGINS HERE
####
#####################################

