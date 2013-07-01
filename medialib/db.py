import sqlite3 as lite;
from torrent import Torrent;
from track import Track;

class MedialibDb:
	"""Provides gateway for database objects retrieval"""

	_con = None #Database connection
	_cur = None #Database cursor

	def __init__(self):
		self._con = lite.connect('data/test.db')
		self._con.row_factory = lite.Row
		self._con.text_factory = str
		self._cur = self._con.cursor()
		self.create_db_structure()

	def create_db_structure(self):
		self._cur.execute("CREATE TABLE IF NOT EXISTS " +
			"torrents(id INTEGER PRIMARY KEY, search_query TEXT, title TEXT, torrent_file TEXT, magnet_link TEXT, created_at TIMESTAMP)")

		self._cur.execute("CREATE TABLE IF NOT EXISTS " +
			"tracks(id INTEGER PRIMARY KEY, torrent_id INT, subfile_no INT, offset INT, size INT, title TEXT, filehash TEXT, created_at TIMESTAMP)")

	def add_torrent(self, torrent_item):	
		self._cur.execute("INSERT INTO torrents (search_query, title, torrent_file, magnet_link, created_at) values (?,?,?,?,?)",
			(torrent_item.search_query, torrent_item.title, torrent_item.torrent_file, torrent_item.magnet_link, torrent_item.created_at)
		)
		id=self._cur.lastrowid
		torrent_item.id = id

		for f in torrent_item.files:
			self.add_track(f)

		self._con.commit()

	def add_track(self, track_item):
		self._cur.execute("INSERT INTO tracks (torrent_id, subfile_no, title, offset, size, filehash, created_at) values (?,?,?,?,?,?,?)",
			(track_item.torrent.id, track_item.subfile_no, track_item.title, track_item.offset, track_item.size, str(track_item.filehash), track_item.created_at)
		)

	def get_torrent_by_query(self, query):
		"""Returns torrents from database that match given query"""
		q = "SELECT * FROM torrents WHERE search_query='"+query+"'";
		list = self._get_torrents_list(q)
		return list[0] if len(list)>0 else False

	def get_all_torrents(self):
		return self._get_torrents_list("SELECT * FROM torrents")

	def _get_torrents_list(self, query):
		self._cur.execute(query)
		rows = self._cur.fetchall()
		result = []

		for row in rows:
			t = Torrent()
			t.id = row["id"]
			t.search_query = row["search_query"]
			t.title = row["title"]
			t.torrent_file = row["torrent_file"]
			t.magnet_link = row["magnet_link"]
			t.created_at = row["created_at"]
			self.load_torrent_tracks(t)
			result.append(t)

		return result;

	def load_torrent_tracks(self, torrent_item):
		query = "SELECT * FROM tracks WHERE torrent_id = " + str(torrent_item.id)
		tracks = self._get_tracks_list(query)
		for t in tracks:
			t.torrent = torrent_item
			torrent_item.files.append(t) 

	def _get_tracks_list(self, query):
		self._cur.execute(query)
		rows = self._cur.fetchall()
		result = []

		for row in rows:
			t = Track()
			t.id = row["id"]
			t.subfile_no = row["subfile_no"]
			t.title = row["title"]
			t.offset = row["offset"]
			t.size = row["size"]
			t.filehash = row["filehash"]
			t.created_at = row["created_at"]
			result.append(t)

		return result;


