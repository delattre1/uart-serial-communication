from enlace import *
import os
import time
import numpy as np
from utils import datagram_builder, receivement_handler
from datagram import Datagram
serialName = "/dev/ttyVirtualS0"

CLIENT_ID = 1
SERVER_ID = 2
FILE_ID = 1


class Server:
    def __init__(self,):
        self.com2 = enlace(serialName)
        self.com2.enable()

    def send_package(self):
        self.com2.sendData(self.package)

    def get_header(self):
        self.r_header, self.len_r_header = self.com2.getData(10)

    def get_payload_eop(self):
        self.package_header = list(self.r_header)
        package_size = 4

        msg_type = self.package_header[0]
        self.n_of_packages = self.package_header[3]
        self.n_of_current_package = self.package_header[4]

        if msg_type == 3:
            payload_size = self.package_header[5]
            package_size += payload_size

        self.r_package, self.len_r_package = self.com2.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

    def server_handshake(self):
        self.get_header()
        self.get_payload_eop()

        print(f'header recebido: {self.r_header}')

        if self.package_header[2] == SERVER_ID:
            print(f'Recebido HS do client - ID correto - server ready\n')
            if self.package_header[0] == 1:
                print(f'mensagem do tipo 1 - fazer funcao pra responder')

                payload = []
                header_list = [0 for i in range(10)]
                header_list[0] = 2  # mensagem to tipo 2 - server ocioso
                header_list[1] = CLIENT_ID
                header_list[2] = SERVER_ID

                datagram_obj = Datagram(payload, header_list)
                self.package = datagram_obj.get_datagram()
                self.send_package()
                print(f'enviado resposta para o client')

                time.sleep(1)
                # self.send_handshake()
        else:
            print(f'ID do servidor não confere, ignorando mensagem...')

    def main(self):
        print(f'Servidor inicializado')
        self.server_handshake()

        time.sleep(1)
        self.com2.disable()


if __name__ == '__main__':
    server = Server()
    server.main()
    os._exit(os.EX_OK)
