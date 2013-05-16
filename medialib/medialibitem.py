

class MediaLibItem(object):
    query = "" #Query that this media item had satisfied
    name = "" #Name of torrent file
    torrent = "" #Torrent file location relative to "torrents/" folder
    magnet = ""
    #Subfiles would be added in future
    
    def __init__(self, query, name, torrent='', magnet=''):
        self.query = query
        self.name = name
        self.torrent = torrent
        self.magnet = magnet