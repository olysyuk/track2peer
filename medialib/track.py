from datetime import datetime

class Track:
	"""Class implements single track instance"""
	torrent = None #Link to torrent record instance
	offset = 0
	size = 0
	title = "" #Track title
	filehash = "" #Will be used to identify file
	created_at = "" #Timestamp of creation

	def __init__(self):
		self.created_at = datetime.now().isoformat(' ')
		pass