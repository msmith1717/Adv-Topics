class Peer:
    def __init__(self, publicKey, ip, port, nonce ):
        self.ip = ip
        self.port = port
        self.nonce = nonce
        self.publicKey = publicKey

    def parseJSON(json):
        return Peer(json['publicKey'], json['ip'], json['port'], json['nonce'])

    def toJSON(self):
        json = {
            "__type__": self.__class__.__name__,
            "ip": self.ip,
            "port": self.port,
            "nonce": self.nonce,
            "publicKey": self.publicKey
        }
        return json