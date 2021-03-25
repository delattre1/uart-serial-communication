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


def build_fake_package_for_test(self):
    self.header_list = [1 for i in range(10)]
    self.header_list[0] = 3  # mensagem to tipo 1 - handshake
    self.header_list[1] = CLIENT_ID
    self.header_list[2] = SERVER_ID

    payload = self.l_bytes_img[index_package]
    self.header_list[3] = len(self.l_bytes_img)
    self.header_list[4] = index_package + 1
    self.header_list[5] = len(payload)

    datagram = Datagram(payload, self.header_list)
    self.l_packages.append(datagram.get_datagram())

    self.len_packages = len(self.l_packages)
