from enlace import *
import os
import time
import numpy as np
from utils import open_image, separate_packages
from datagram import Datagram

serialName = "/dev/ttyVirtualS1"

CLIENT_ID = 1
SERVER_ID = 2
FILE_ID = 1


class Client:
    def __init__(self, path):
        self.com1 = enlace(serialName)
        self.com1.enable()
        self.img_array = open_image(path)
        self.l_bytes_img = separate_packages(self.img_array)
        self.l_packages = []

    def send_package(self):
        self.com1.sendData(self.package)

    def build_packages(self):
        for i in range(len(self.l_bytes_img)):
            payload = self.l_bytes_img[i]
            header = [1 for i in range(10)]

            datagram = Datagram(payload, header)
            self.l_packages.append(datagram.get_datagram())

    def send_package(self):
        self.com1.sendData(self.package)

    def get_header(self):
        self.r_header, self.len_r_header = self.com1.getData(10)

    def get_payload_eop(self):
        self.package_header = list(self.r_header)
        msg_type = self.package_header[0]
        package_size = 4

        msg_type = self.package_header[0]

        self.n_of_packages = self.package_header[3]
        self.n_of_current_package = self.package_header[4]

        self.r_package, self.len_r_package = self.com1.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

    def client_handshake(self):
        payload = []
        header_list = [0 for i in range(10)]

        header_list[0] = 1  # mensagem to tipo 1 - handshake
        header_list[1] = CLIENT_ID
        header_list[2] = SERVER_ID
        header_list[3] = len(self.l_packages)
        header_list[5] = FILE_ID

        datagram_obj = Datagram(payload, header_list)
        datagram = datagram_obj.get_datagram()

        self.package = datagram

        print(f'Enviando handshake para o Servidor..')
        self.send_package()

        self.start_time = time.time()
        while self.com1.rx.getBufferLen() == 0:
            self.time_delta = time.time() - self.start_time
            if self.time_delta >= 5:
                should_send_again = input(
                    'Didn\'t receive response. Send again? (s/n) ')
                if should_send_again == 's':
                    print(f'Enviando novamente...\n')
                    self.send_package()
                    self.start_time = time.time()
                else:
                    os._exit(os.EX_OK)

        self.get_header()
        self.get_payload_eop()
        if self.package_header[0] == 2:
            print(f'Server está ocioso... começando o envio\n')

    def main(self):
        self.build_packages()

        self.client_handshake()
        # for pak in self.l_packages:
        #    print(f'lista com os pacotes: {pak}\n\n')

        time.sleep(0.5)
        self.com1.disable()


if __name__ == '__main__':
    client = Client('imgs/advice.png')
    client.main()
    os._exit(os.EX_OK)
