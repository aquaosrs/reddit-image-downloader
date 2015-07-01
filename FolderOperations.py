import os
from distutils.dir_util import mkpath

def CreateDir(Path):
	# Check if directory exists and create it if not.
	Path = Path.rstrip()
	if not os.path.exists(Path):
		try:
			mkpath(Path)
		except:
			print "Cannot Create DIR"

def DeleteDir(Path):
	if not os.path.exists(Path):
		try:
			os.rmdir(Path)
		except:
			pass

def RemoveEmptyFolders(path):
	path = os.path.relpath(path)
	if not os.path.isdir(path):
		return

	# remove empty subfolders
	files = os.listdir(path)
	if len(files):
		for f in files:
			fullpath = os.path.join(path, f)
			if os.path.isdir(fullpath):
				RemoveEmptyFolders(fullpath)

	# if folder empty, delete it
	files = os.listdir(path)
	if len(files) == 0:
		print "Removing empty folder:", path
		DeleteDir(path)
