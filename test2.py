import glob
import os
import sys
import time
import thread
from outsearch import OutSearch
from medialib import Torrent


def play():
    sample_dir = 'sample/'
    print "Select one of the available files:"

    torrent_files = glob.glob(sample_dir+'*')
    for i,v in enumerate(torrent_files):
        print i, ' ', v

    tf = int(raw_input("Please enter torrent number: "))


    import player
    tp = player.TorrentPlayer()
    tp.load_filepath(torrent_files[tf])

    t = Torrent()
    t.torrent_file = torrent_files[tf]
    OutSearch().loadFilesList(t)

    subfiles = t.files
    for v in subfiles:
        print v.subfile_no, ' ', v.title

    sf = int(raw_input("Please enter subfile number: "))

    tp.select_file(sf)
    thread.start_new_thread(tp.play,())
    return tp