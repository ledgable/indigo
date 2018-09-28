
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

import calendar, datetime

import string, cgi, time
import threading
import json
import ssl
import base64
import errno
import http.client

from OpenSSL import SSL
from OpenSSL.SSL import TLSv1_METHOD, Context, Connection

import sys, getopt, imp, traceback

from pytz import timezone
from os import curdir, sep

from io import StringIO
from xml.dom.minidom import Document
from decimal import Decimal

from signal import *
from netifaces import AF_INET, AF_INET6, AF_LINK

import netifaces as ni

from netaddr import IPNetwork, IPAddress
from socketserver import ForkingMixIn, ThreadingMixIn
from concurrent.futures import ThreadPoolExecutor

from urllib.parse import urlparse, parse_qs

from http.cookies import SimpleCookie as cookie
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from http import cookies

from twisted.internet import reactor
from twisted.internet import ssl as tSSL

from threading import Timer, Thread
from time import sleep

from modules.baseclass import *
from modules.repeater import *
from modules.daoobject import *
from modules.singleton import *
from modules.ipblocker import *

from .applicationhandler import *
from .functionresponse import *

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/../../../"

class CoreHandler(BaseClass, BaseHTTPRequestHandler):
	
	useSSL = False
	transactionid_ = None
	timestart_ = 0


	@property
	def socket(self):
		try:
			if self.socket_ != None:
				return self.socket_
		except Exception as inst:
			pass
		return None


	def __init__(self, request, client_address, server, country_code, isssl=False):
		
		self.country_code = country_code
		self.socket_ = request
		self.timestart_ = self.epoch
		self.useSSL = isssl
		
		BaseHTTPRequestHandler.__init__(self, request, client_address, server)


	@property
	def protocol_version(self):
		
		return "HTTP/1.0"


	@property
	def transactionid(self):
		
		if self.transactionid_ == None:
			self.transactionid_ = uuid.uuid4().hex
		
		return self.transactionid_


	@property
	def ipaddress(self):
		return self.client_address[0]


	def log_message(self, format, *args):
		return


class CoreServer(BaseClass, ThreadingMixIn):
	
	allow_reuse_address = True
	daemon_threads = True
	config_ = None
	defaultcontext_ = None
	
	instanceid = 0
	
	port_ = 0
	timer_ = None
	run_ = False
	sslContexts_ = None


	def finish_request(self, request, client_address, country_code, isssl):
		pass


	def process_request_thread(self, request, client_address, country_code, isssl):
		
		try:
			if (request != None):
				self.finish_request(request, client_address, country_code, isssl)
		except:
			if request != None:
				self.handle_error(request, client_address)
		finally:
			if request != None:
				self.shutdown_request(request)


	def process_request(self, request, client_address, country_code, isssl):
	
		t = threading.Thread(target = self.process_request_thread, args=(request, client_address, country_code, isssl))
		t.daemon = self.daemon_threads
		t.start()


	def poller(self, args):
	
		# check transactions for expiry...
		
		now_ = self.epoch
		transactionstocheck_ = list(self.requests_.keys())
		
		if len(transactionstocheck_) > 0:
			for transactionid_ in transactionstocheck_:
				
				request_ = self.requestById(transactionid_)
				newtime_ = now_ - request_.timestart_
				
				if newtime_ > 10:
					self.removeRequestWithTransaction(transactionid_)
					self.log(("Closing transaction - been open too long - %s" % transactionid_), "info")
					request_.server.shutdown_request(request_.request)


	def requestById(self, transactionid):
		if transactionid in self.requests_.keys():
			return self.requests_[transactionid]
			return None


	def addRequestWithTransaction(self, request):
		transactionid_ = request.transactionid
		if transactionid_ not in self.requests_.keys():
			self.requests_[transactionid_] = request


	def removeRequestWithTransaction(self, transactionid):
		if transactionid in self.requests_.keys():
			request_ = self.requests_[transactionid]
			del self.requests_[transactionid]
			request_ = None


	@property
	def requests(self):
		return self.requests_


	def server_bind(self, portin=80):
		
		self.port_ = portin
		self.config_ = DAOObject({})
		
		self.log("Beginning Binding of server on port %d" % (self.instanceid))
		
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.setblocking(0)
		
		self.polltime_ = 0
		self.requests_ = {}
		self.sslContexts_ = {}
		
		HTTPServer.server_bind(self)
		
		self.socket.settimeout(5)
		
		self.run_ = True
		self.timer_ = Repeater(30.0, self.poller, self)
		self.timer_.start()


	def handle_timeout(self):
	
		self.log(("A timeout has occurred in the socket manager"), "info")
	
	
	def ssl_contextForHostname(self, url=None):
		
		contextOut_ = None
		
		if (url in self.sslContexts_.keys()):
			contextOut_ = self.sslContexts_[url]
	
		else:
			sitefound_ = None
			allsites_ = dict(AppHandler().sites)
			
			for site_, handler_ in allsites_.items():
				if (url in handler_.CONFIG.HOST_NAMES):
					sitefound_ = handler_
		
			if (sitefound_ != None):
				contextout_ = self.ssl_context(sitefound_)
				
				if (contextout_ != None):
					self.sslContexts_[url] = contextout_

		return contextOut_


	def ssl_context(self, handler=None):
	
		context_ = None
		
		if (handler != None):
			
			file_ = ("%s/%s/certs/%s" % (ROOT, handler.directory_, "cert.pem"))
			
			if (os.path.exists(file_)):
				
				self.log("SSL context from file = %s for site %s" % (file_, handler.site_))
				
				context_ = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
				context_.set_ecdh_curve('prime256v1')
				context_.set_ciphers(SSL_CIPHERS)
				context_.options |= ssl.OP_NO_COMPRESSION
				context_.options |= ssl.OP_SINGLE_ECDH_USE
				context_.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
				context_.load_cert_chain(certfile=file_)
	
		return context_


	def verify_request(self, request, client_address):
		
		if (client_address != None) and (len(client_address) > 0):
			success_, countrycode_ = IPBlocker().check(client_address[0], "web")
			
			return success_, countrycode_
				
		return False, None
	
	def _verify_callback(cnx, x509, err_no, err_depth, return_code):
		
		return (err_no == 0)


	def get_request(self):
	
		ipaddress_ = IP_LOCALHOST
		sock = None
		addr = None
		isssl = False
		sslsock = None
		dup = None
		
		try:
			sock, addr = self.socket.accept()
			sock.setblocking(0)
			sock.settimeout(3)
	
		except Exception as inst:
			self.logException(inst)
		
		if (sock != None):
			
			if (sock.proto != 0) or (sock.family != AF_INET) or (sock.fileno() == -1):
				sock.close()
				return sock, addr, False

			# we do a simple wrap - if it fails, we pass...

			if (self.instanceid == 443):

				# this is where we map the certificate based upon the incoming host identifier
				
				def servercallback(sock, req_hostname, cb_context, as_callback=True, base=self):
					context = base.ssl_contextForHostname(req_hostname)
					
					if (context is not None):
						sock.context = context
					else:
						pass
				
				try:
					if (self.defaultcontext_ == None):
						
						context_ = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
						context_.set_ciphers(SSL_CIPHERS)
						context_.options |= ssl.OP_NO_COMPRESSION
						context_.options |= ssl.OP_SINGLE_ECDH_USE
						context_.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
						context_.set_servername_callback(servercallback)
						
						self.defaultcontext_ = context_
					
					sslsock = self.defaultcontext_.wrap_socket(sock.dup(), server_side=True)
					sock = sslsock
					isssl = True
				
				except ssl.SSLError as e:
					
					if (e.errno == ssl.SSL_ERROR_EOF):
						# This is almost certainly due to the cherrypy engine
						# 'pinging' the socket to assert it's connectable;
						# the 'ping' isn't SSL.						
						return None, {}, False
					
					elif (e.errno == ssl.SSL_ERROR_SSL):
						
						if e.args[1].endswith('http request'):
							self.log("HTTP Request over SSL")
							# The client is speaking HTTP to an HTTPS server.
							return sock, addr, False
						
						elif e.args[1].endswith('unknown protocol'):
							# The client is speaking some non-HTTP protocol.
							# Drop the conn.
							self.log("Unknown Protocol")
							return None, {}, False
				
					else:
						return None, {}, False

				except Exception as inst:
					self.log("An exception occurred")

		if (sock != None):
			if (sock.fileno() != -1):
				sock.settimeout(255)

		return sock, addr, isssl


	def _handle_request_noblock(self):
	
		request = None
		client_address = None
		isssl = False
		handler = None
		
		try:
			request, client_address, isssl = self.get_request()
	
		except OSError as inst:
			self.logException(inst)
		
			if (request != None):
				self.handle_error(request, client_address)
				self.shutdown_request(request)

			return
	
		except Exception as inst:
			self.logException(inst)
			
			if (request != None):
				self.handle_error(request, client_address)
				self.shutdown_request(request)
			
			return
		
		requestvalid_, country_code = self.verify_request(request, client_address)
		
		if (requestvalid_):
			
			try:
				self.process_request(request, client_address, country_code, isssl)
			
			except Exception:
				if (request != None):
					self.handle_error(request, client_address)
					self.shutdown_request(request)
		
			except:
				if (request != None):
					self.shutdown_request(request)
				raise

		else:
			if (request != None):
				self.shutdown_request(request)


	def close_request(self, request):
	
		if (request is None):
			return
		
		HTTPServer.close_request(self, request)


	def stop(self):
		
		self.run_ = False


	def serve(self):
	
		while self.run_:
			try:
				r,w,e = select.select([self.socket], [], [], 2.0)
				if r:
					self._handle_request_noblock()
			
			except Exception as inst:
				pass

