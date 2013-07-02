track2peer
==========

Overview
--------

With help of this library you can easily find, download songs and albums from popular torrent trackers. Even if yo go offline, all your previous tracks are stored on your computer, so they are available everywhere.

Installation
------------

Here is installation instructions for Ubuntu. It's also working on mac.

Track2Peer requires libtorrent, mplayer and sqlite3 to work.

```
>apt-get install python-libtorrent
>apt-get install sqlite
>apt-get install mplayer
```

see more details at [http://packages.ubuntu.com/raring/python-libtorrent]

Demo usage
----------

Since library is on development, deep code reading might be required to get all neede features.
Here is a simple example of how it works

Example
```
>python test.py
Please enter song or artist name: SampleArtist
Searching SampleArtist
Searching online
Fetching torrent metadata
0 track1
1 track2
2 track3
select track number: 0
download progress 0%..5% (playback starts where track is still downloading)


--- On the second run
>python test.py
Please enter song or artist name: SampleArtist
Searching SampleArtist
Found on database
0 track1
1 track2
2 track3
select track number: 0
--->playing track without download
```


Example 2:
```
>python
> import test2
> tp = test2.play()
> tp.pause()
> tp.stop()
```