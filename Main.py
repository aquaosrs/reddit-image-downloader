from urllib2 import urlopen, HTTPError, URLError, Request
import os, json, urllib2
from argparse import ArgumentParser
from sys import argv
from requests import get
from re import sub
from distutils.dir_util import mkpath

global CurrentSubReddit
CurrentSubReddit = ""
global CurrentDir
CurrentDir = ""
Path = "Reddit Rips"
SupportedExts = ['.jpg', '.jpeg', '.png', '.gif']
ImgurAfterString = '" target="_blank">View full resolution</a>'
ImgurBeforeString = '<a href="//i.imgur.com/'
ImgurAlbumString = 'imgur.com/a/'
BeginingImgurPictureUrl = 'http://i.imgur.com/'

global PageStatsDownloaded
PageStatsDownloaded = 0
global PageStatsAlreadyGot
PageStatsAlreadyGot = 0
global PageStatsFailed
PageStatsFailed = 0

global TotalPageStatsDownloaded
TotalPageStatsDownloaded = 0
global TotalPageStatsAlreadyGot
TotalPageStatsAlreadyGot = 0
global TotalPageStatsFailed
TotalPageStatsFailed = 0

def PrintPage(SubReddit, Number):
	print '---------------------------------------------'
	print SubReddit + ' Page: ' + str(Number)
	print '---------------------------------------------'

def PrintSubReddit(SubReddit, Sort):
	print '---------------------------------------------'
	print 'Downloading SubReddit: ' + SubReddit + ' Sorted by: ' + Sort
	
def PrintStats():
	global PageStatsDownloaded
	global PageStatsAlreadyGot
	global PageStatsFailed
	global TotalPageStatsDownloaded
	global TotalPageStatsAlreadyGot
	global TotalPageStatsFailed
	print '---------------------------------------------'
	if not (PageStatsDownloaded + PageStatsAlreadyGot + PageStatsFailed) == 0:
		print 'Page Downloaded:'
		print 'Downloaded Images: ' + str(PageStatsDownloaded)
		TotalPageStatsDownloaded += PageStatsDownloaded
		PageStatsDownloaded = 0
		print 'Images Already Got: ' + str(PageStatsAlreadyGot)
		TotalPageStatsAlreadyGot += PageStatsAlreadyGot
		PageStatsAlreadyGot = 0
		print 'Images Failed: ' + str(PageStatsFailed)
		TotalPageStatsFailed += PageStatsFailed
		PageStatsFailed = 0
	else:
		print 'Page Skipped: No Links Found'

def PrintTotalStats():
	global TotalPageStatsDownloaded
	global TotalPageStatsAlreadyGot
	global TotalPageStatsFailed
	print '---------------------------------------------'
	if not (TotalPageStatsDownloaded + TotalPageStatsAlreadyGot + TotalPageStatsFailed) == 0:
		print 'Total Downloaded Images: ' + str(TotalPageStatsDownloaded)
		TotalPageStatsDownloaded = 0
		print 'Total Images Already Got: ' + str(TotalPageStatsAlreadyGot)
		TotalPageStatsAlreadyGot = 0
		print 'Total Images Failed: ' + str(TotalPageStatsFailed)
		TotalPageStatsFailed = 0
	else:
		print 'Page Skipped: No Links Found'

def CreateDir(Path=Path):
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
		os.rmdir(path)

def SetCurrentDir():
	global CurrentDir
	CurrentDir = os.path.join(Path, CurrentSubReddit)
	CreateDir(CurrentDir)
	
def SetCurrentSubReddit(SubReddit):
	global CurrentSubReddit
	CurrentSubReddit = SubReddit
	CreateDir()
	SetCurrentDir()

def download_imgur_album(url):
	album_id = url[url.index(ImgurAlbumString) + len(ImgurAlbumString):]
	AlbumDIR = os.path.join(CurrentDir, album_id)
	CreateDir(AlbumDIR)
	
	count = 0
	AfterIndex = 0

	try:
		response = urllib2.urlopen(url)
	except:
		global PageStatsFailed
		PageStatsFailed += 1
		return False
	
	html = response.read()
	AlbumSize = html.count(ImgurAfterString)
	while count < AlbumSize:
		count += 1;
		AfterIndex = html.index(ImgurAfterString, AfterIndex)
		BeforeIndex = html.index(ImgurBeforeString, AfterIndex - 120)
		BeforeIndex = BeforeIndex + len(ImgurBeforeString)
		
		url = BeginingImgurPictureUrl + html[BeforeIndex:AfterIndex]
		
		if not any(url.endswith(ext) for ext in SupportedExts):
			if any(ext in url for ext in SupportedExts):
				for ext in SupportedExts:
					IndexOfAnomaly = url.find(ext)
					if not IndexOfAnomaly == -1:
						url = url[:IndexOfAnomaly + len(ext)]
		
		AfterIndex = AfterIndex + len(ImgurAfterString)
		
		image_name = sub(".*\/", "", url)
		filepath = os.path.join(AlbumDIR, image_name)
		filepath = filepath.replace("/", "\\");
		
		download_file(url, filepath)

def handle_imgur_url(url):
	"""
	Takes Imgur URL and checks if direct link has correct extension. 
	"""
	if ImgurAlbumString in url:
		if any(not url.endswith(ext) for ext in SupportedExts):
			download_imgur_album(url)
			return False
	
	# all static imgur files are jpegs so use .jpg extension
	if url.endswith('.png'):
		url = url.replace('.png', '.jpg')
	else:
		# if no extension, add .jpg
		ext = os.path.splitext(os.path.basename(url))[1]
		if not ext:
			url += '.jpg'
	return [url]

def get_urls(url):
	""" Checks to see if URL is imgur.com and handles, otherwise 
	simply returns the given url in a list (for planned imgur gallery suppory).
	"""

	urls = []

	# is valid imgur.com url
	if 'imgur.com' in url:
		tempurl = handle_imgur_url(url)
		if not tempurl == False:
			   urls = tempurl
	elif any(url.endswith(Exts) for Exts in SupportedExts):
		urls = [url]

	return urls

def get_items(subreddit, limit, sort, count=0, after=""):
	""" Returns a list of items from a subreddit, optionally sorted by
	hot, new, controversial or top. """

	BASE_URL = 'http://www.reddit.com/r/%s/%s.json?count=%s&limit=%s&after=t3_%s' % (subreddit, sort, count, limit, after)

	HEADER = { 'User-Agent' : 'RipReddit script' }

	try: 
		request = Request(BASE_URL, headers=HEADER)
		raw_json = urlopen(request).read()
		json_data = json.JSONDecoder().decode(raw_json)
		items = [x['data'] for x in json_data['data']['children']]
	except HTTPError as ERROR:
		print '\t%s HTTP Error received for %s' % (ERROR.code, BASE_URL)
		items = []
	except:
		global PageStatsFailed
		PageStatsFailed += 1
		items = []
	return items

def download_file(url, filepath):
	""" Try and download the file from the URL and save to 'filepath'

	It will not download the same file more than once
	"""
	
	ext_whitelist = ['image/jpeg', 'image/png', 'image/gif']

	try:
		with open(filepath):
			global PageStatsAlreadyGot
			PageStatsAlreadyGot += 1
	except IOError:
		try:
			response = urlopen(url)
			info = response.info()

			# Check file type
			if 'content-type' in info.keys():
				filetype = info['content-type']
			elif url.endswith('.jpg') or url.endswith('.jpeg'):
				filetype = 'image/jpeg'
			elif url.endswith('.png'):
				filetype = 'image/png'
			elif url.endswith('.gif'):
				filetype = 'image/gif'
			else:
				filetype = 'unrecognised'

			if not filetype in ext_whitelist:
				print "URL (%s) has incorrect file type: %s" % (url, filetype)

			global PageStatsDownloaded
			PageStatsDownloaded += 1
                        
			filedata = response.read()
			filehandle = open(filepath, 'wb')
			filehandle.write(filedata)
			filehandle.close()
		except:
			print "Not Entirely sure why this url failed to download: " + url
			global PageStatsFailed
			PageStatsFailed += 1
			
def DownloadSubRedditPage(SubReddit, path, Count, After, Sort, Limit=100):
	Count = Count * Limit
	items = get_items(SubReddit, Limit, Sort, Count, After)
	
	for item in items:
		urls = get_urls(item['url'])

		for url in urls:
			# Set filename and try to download file
			try:
				
				# Remove any HTTP queries from end of url to get clean ext
				ext = os.path.splitext(url)[1]
				if '?' in ext:
					ext = ext[:ext.index('?')]

				filename = '%s%s' % (item['id'], ext)
				filepath = os.path.join(path, filename)

				After = item['id']
				download_file(url, filepath)

			except HTTPError as e:
				#print '\tReceived HTTP Error (%s) from %s' % (e.code, url)
				global PageStatsFailed
				PageStatsFailed += 1
	return After

def DownloadSubReddit(SubReddit, NumberOfPagesToGet = 1, Sort='hot'):
	PrintSubReddit(SubReddit, Sort)
	SetCurrentSubReddit(SubReddit)
	path = os.path.join(Path, SubReddit)
	CreateDir(path)
	Count = 0
	FailedCount = 0
	After = ''
	while Count < NumberOfPagesToGet:
		PrintPage(SubReddit, Count + 1)
		After = DownloadSubRedditPage(SubReddit, path, Count, After, Sort)
		Count += 1
		if(PageStatsDownloaded + PageStatsAlreadyGot + PageStatsFailed == 0):
			FailedCount += 1
			if(FailedCount == 3):
				Count += NumberOfPagesToGet
				
		RemoveEmptyFolders(CurrentDir)
		PrintStats()

def ReadFromFile(TextFilePath = os.path.join(Path, 'Subreddits.txt'), Sort='hot'):
	TextFile = open(TextFilePath, 'r')
	SubRedditList = TextFile.readlines()
	for SubReddit in SubRedditList:
		SubReddit = SubReddit.rstrip()
		DownloadSubReddit(SubReddit, 10, Sort)
		PrintStats()

ReadFromFile()

PrintTotalStats()
