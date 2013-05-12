import glob
import os


sample_dir = 'sample/'
print "Select one of the available files:"

torrent_files = glob.glob(sample_dir+'*')
for i,v in enumerate(torrent_files):
    print i, ' ', v

tf = int(raw_input("Please enter torrent number: "))


import player
tp = player.TorrentPlayer()
tp.load_torrent(torrent_files[tf])

subfiles = tp.get_files_list()
for i,v in enumerate(subfiles):
    print i, ' ', v

sf = int(raw_input("Please enter subfile number: "))

tp.select_file(sf)
tp.play()

while True:
    pass