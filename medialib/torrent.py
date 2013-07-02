from datetime import datetime
from track import Track

class Torrent(object):
	"""Model for torrent file. Subfiles are presented as tracks"""
	id = None
	search_query = "" #Query that this media item had satisfied
	title = "" #Title of torrent file
	torrent_file = "" #Torrent file location relative to "sample/" folder
	magnet_link = "" #URI of magnet link
	created_at = "" #Timestamp of creation
	files = [] #Files list

	def __init__(self):
		self.created_at = datetime.now().isoformat(' ')

	def set_files(self, files_list):
		for i,f in enumerate(files_list):
			t = Track()
			t.subfile_no = i
			t.torrent = self
			t.offset = f.offset
			t.size = f.size
			t.title = f.path 
			t.filehash = f.filehash
			self.files.append(t)