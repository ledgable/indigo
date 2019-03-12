
import os
import os.path
import hashlib

from os import curdir, sep, path

def filemd5(filename=None):
			
	if (filename != None) and (os.path.exists(filename)):

		data_ = None

		with open(filename, 'rb') as fileRead:
			data_ = fileRead.read()

		hashval_ = hashlib.md5()
		hashval_.update(data_)
		
		return hashval_.hexdigest()

	return None


