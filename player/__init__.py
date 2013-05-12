"""This package contains player, current usage is
    tp = new TorrentPlayer()
    tp.load_torrent('example.torrent')
    tp.get_files_list() #returns list of get_files
    tp.select_file(i) #set file that would be played
    tp.play()
"""

from player import Player
from torrentplayer import TorrentPlayer
__all__=['TorrentPlayer']


