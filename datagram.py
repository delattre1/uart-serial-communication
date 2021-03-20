import numpy as np

ZERO = bytes([0])
FF = bytes([255])
AA = bytes([170])


class Datagram:
    def __init__(self, payload, header_list):
        self.header = [bytes([i]) for i in header_list]
        self.payload = payload
        self.eop = [FF, AA, FF, AA]

    def get_datagram(self):
        self.datagram = self.header + self.payload + self.eop
        return np.asarray(self.datagram)
