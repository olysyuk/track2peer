import glob
import os
import sys
import time
import thread


def testplay():
    sample_dir = 'sample/'
    print "Select one of the available files:"

    torrent_files = glob.glob(sample_dir+'*')
    for i,v in enumerate(torrent_files):
        print i, ' ', v

    tf = int(raw_input("Please enter torrent number: "))


    import player
    tp = player.TorrentPlayer()
    tp.load_filepath(torrent_files[tf])

    subfiles = tp.get_files_list()
    for i,v in enumerate(subfiles):
        print i, ' ', v

    sf = int(raw_input("Please enter subfile number: "))

    tp.select_file(sf)
    #tp.play()
    thread.start_new_thread(tp.play,())

    while True:
        print repr(round(tp._download_progress*100)).rjust(6),"% is ready ",
        sys.stdout.flush()
        time.sleep(1)
        print "\r",
        if (tp._download_progress==1): 
            print "File is ready               "
            break
        pass
