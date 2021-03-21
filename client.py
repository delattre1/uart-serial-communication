from enlace import *
import os
import time
import numpy as np
from utils import open_image, separate_packages, get_current_time
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
        msg_type = self.header_list[0]
        current_time = get_current_time()
        self.str_log = f'{current_time} | envio |{msg_type} | tamanho_arrumar | pacote_enviado | total_pacote | CRC \n'
        self.write_logs()

    def write_logs(self):
        with open('log1_client.txt', 'a') as fd:
            fd.write(self.str_log)

    def build_packages(self):
        for index_package in range(len(self.l_bytes_img)):
            payload = self.l_bytes_img[index_package]
            self.header_list = [1 for i in range(10)]

            self.header_list[0] = 3  # mensagem to tipo 1 - handshake
            self.header_list[1] = CLIENT_ID
            self.header_list[2] = SERVER_ID
            self.header_list[3] = len(self.l_bytes_img)
            self.header_list[4] = index_package + 1
            self.header_list[5] = len(payload)

            datagram = Datagram(payload, self.header_list)
            self.l_packages.append(datagram.get_datagram())

        self.len_packages = len(self.l_packages)

    def get_header(self):
        self.r_header, self.len_r_header = self.com1.getData(10)

    def get_payload_eop(self):
        self.package_header = list(self.r_header)
        msg_type = self.package_header[0]
        package_size = 4

        msg_type = self.package_header[0]

        if msg_type == 5:
            print(f'Recebido sinal de desligamento da outra parte...')
            print(f'Encerrando o processo')
            os._exit(os.EX_OK)

        self.n_of_packages = self.package_header[3]
        self.n_of_current_package = self.package_header[4]

        self.r_package, self.len_r_package = self.com1.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

    def client_handshake(self):
        payload = []
        self.header_list = [0 for i in range(10)]

        self.header_list[0] = 1  # mensagem to tipo 1 - handshake
        self.header_list[1] = CLIENT_ID
        self.header_list[2] = SERVER_ID
        self.header_list[3] = len(self.l_packages)
        self.header_list[5] = FILE_ID

        datagram_obj = Datagram(payload, self.header_list)
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

    def send_full_packages(self):
        for index_package in range(self.len_packages):
            self.package = self.l_packages[index_package]
            self.send_package()
            self.timer1 = time.time()
            self.timer2 = self.timer1
            print(f'Enviando o pacote [{index_package + 1}]...')
            self.verify_server_receivement()

    def verify_server_receivement(self):
        msg_type = ''
        while msg_type != 4:

            # loops until notice something in the buffer, then verify
            while self.com1.rx.getBufferLen() == 0:
                current_time = time.time()
                elapsed_timer1 = current_time - self.timer1
                elapsed_timer2 = current_time - self.timer2

                if elapsed_timer1 >= 20:
                    print(f'Tempo máximo excedido, avisando server desligamento...')
                    payload = []

                    self.header_list = [1 for i in range(10)]
                    self.header_list[0] = 5  # mensagem to tipo 1 - handshake
                    self.header_list[1] = CLIENT_ID
                    self.header_list[2] = SERVER_ID

                    datagram_obj = Datagram(payload, self.header_list)
                    self.package = datagram_obj.get_datagram()
                    self.send_package()

                    time.sleep(1)

                    os._exit(os.EX_OK)

                if elapsed_timer2 >= 5:
                    print(f'5 segundos sem resposta, enviando novamente...')
                    self.send_package()
                    self.timer2 = time.time()

            self.get_header()
            self.get_payload_eop()
            msg_type = self.package_header[0]
            print(f'Tipo msg: {msg_type}')

            if msg_type == 4:
                print(f'Server recebeu corretamente o pacote. Enviando o próximo')

            elif msg_type == 6:
                print(f'Server nao recebeu corretamente. Reenviando...')
                self.send_package()
                self.timer2 = time.time()

    def main(self):
        self.build_packages()

        self.client_handshake()

        self.send_full_packages()
        time.sleep(0.5)
        self.com1.disable()


if __name__ == '__main__':
    client = Client('imgs/advice.png')
    client.main()
    os._exit(os.EX_OK)
