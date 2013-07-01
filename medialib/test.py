from db import MedialibDb;
from torrent import Torrent;


medialib = MedialibDb();

torrent = Torrent()
torrent.title = 'test'
torrent.magnet_uri = 'sfewfwefewfewfwfewf'

print medialib.get_torrents_list()

medialib.add_torrent(torrent)

print torrent.id
print medialib.get_torrents_list()