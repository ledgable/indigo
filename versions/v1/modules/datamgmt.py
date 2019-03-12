
import json

from struct import *
from config import *

from .switch import *

# management of datawriting / reading for the rest of the application

class MessageReader:
	
	def f(self, x):
		
		for case in switch(x):
			
			if case("S"):
				return self.readString
			
			if case("I"):
				return self.readInt
			
			if case("L"):
				return self.readLong
			
			if case("D"):
				return self.readDouble
			
			if case("F"):
				return self.readFloat
			
			if case("B"):
				return self.readByte
			
			if case("Y"):
				return self.readBytes
	
		return None
			
	def __init__(self, data):
		self.data = data
		self.offset = 0
	
	def reset(self):
		self.offset = 0

	@property
	def readByte(self):
		
		retval = unpack('!B', self.data[self.offset:self.offset+1])[0]
		self.offset += 1
		return retval
	
	@property
	def readBytes(self):
		
		quantity = unpack('!q', self.data[self.offset:self.offset+8])[0]
		self.offset += 8
		retval = self.data[self.offset:self.offset+quantity]
		self.offset += quantity
		return retval

	@property
	def readFloat(self):
		
		retval = unpack('f', self.data[self.offset:self.offset+4])[0]
		self.offset += 4
		return retval

	@property
	def readDouble(self):
		
		retval = unpack('d', self.data[self.offset:self.offset+8])[0]
		self.offset += 8
		return retval
	
	@property
	def readInt(self):
		
		retval = unpack('!I', self.data[self.offset:self.offset+4])[0]
		self.offset += 4
		return retval

	@property
	def readLong(self):
		
		retval = unpack('!q', self.data[self.offset:self.offset+8])[0]
		self.offset += 8
		return retval

	@property
	def readString(self):
		
		strLength = self.readInt
		unpackStr = '!%ds' % (strLength-1)
		retval = unpack(unpackStr, self.data[self.offset:self.offset+(strLength-1)])[0]
		self.offset += strLength
		
		out_ = retval.decode(UTF8)
		if (out_ == NULL_VAR):
			return None
		
		return out_
	
class MessageWriter:

	def __init__(self):
		
		self.data = b""

	def writeByte(self, value):
		
		self.data += pack('!B', value)

	def writeBytes(self, value):
		
		length = len(value)
		self.writeLong(length)
		self.data += value

	def writeFloat(self, value):
		
		self.data += pack('f', value)

	def writeDouble(self, value):
		
		self.data += pack('d', value)
	
	def writeInt(self, value):
		
		self.data += pack('!I', value)

	def writeLong(self, value):
		
		self.data += pack('!q', value)

	def writeString(self, value):
		
		if value == None:
			value = NULL_VAR
		
		if value != "":
			if (value[-1] != b"\0"):
				value += "\0"
		
		else:
			value += "\0"
		
		string_ = bytes(value, UTF8)
		self.writeInt(len(string_))
		packStr = '!%ds' % (len(string_))
		self.data += pack(packStr, string_)

