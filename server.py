from enlace import *
import os
import time
import numpy as np
from datagram import Datagram
serialName = "/dev/ttyVirtualS0"

CLIENT_ID = 1
SERVER_ID = 2
FILE_ID = 1


class Server:
    def __init__(self,):
        self.com2 = enlace(serialName)
        self.com2.enable()
        self.l_received_payloads = []

    def send_package(self):
        self.com2.sendData(self.package)

    def get_header(self):
        self.r_header, self.len_r_header = self.com2.getData(10)

    def get_payload_eop(self):
        self.package_header = list(self.r_header)
        package_size = 4

        msg_type = self.package_header[0]
        self.n_of_packages = self.package_header[3]
        self.n_current_package = self.package_header[4]

        if msg_type == 3:
            payload_size = self.package_header[5]
            package_size += payload_size

        if msg_type == 5:
            print(f'Recebido sinal de desligamento da outra parte...')
            print(f'Encerrando o processo')
            os._exit(os.EX_OK)

        self.r_package, self.len_r_package = self.com2.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

    def server_handshake(self):
        self.get_header()
        self.get_payload_eop()
        self.quantity_packages_to_receive = self.package_header[3]
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

    def build_response(self):
        is_package_ok = self.is_next_package and self.is_eop_right
        payload = []
        header_list = [0 for i in range(10)]

        if is_package_ok:  # create type4  msg representing that the package was received successfully
            self.l_received_payloads.append(self.r_payload)
            print(f'package [{self.n_current_package}] received correctly')
            self.n_last_package_received = self.n_current_package
            header_list[0] = 4  # mensagem to tipo 1 - handshake
            header_list[1] = CLIENT_ID
            header_list[2] = SERVER_ID
            header_list[7] = self.n_last_package_received
        else:
            print(
                f'package [{self.n_current_package}] had some error, requesting again..')
            header_list[0] = 6  # mensagem to tipo 6 - solicitando reenvio
            header_list[1] = CLIENT_ID
            header_list[2] = SERVER_ID
            header_list[6] = self.n_last_package_received + 1

        datagram_obj = Datagram(payload, header_list)
        self.package = datagram_obj.get_datagram()

    def receive_full_packages(self):

        self.n_last_package_received = 0

        while self.n_current_package < self.quantity_packages_to_receive:
            while self.com1.rx.getBufferLen() == 0:
                self.timer1 = time.time()
                self.timer2 = self.timer1

                if elapsed_timer1 >= 20:
                    print(f'Tempo máximo excedido, avisando client desligamento...')
                    payload = []

                    header_list = [1 for i in range(10)]
                    header_list[0] = 5  # mensagem to tipo 1 - handshake
                    header_list[1] = CLIENT_ID
                    header_list[2] = SERVER_ID

                    datagram_obj = Datagram(payload, header_list)
                    self.package = datagram_obj.get_datagram()
                    self.send_package()

                    time.sleep(1)
                    os._exit(os.EX_OK)

                if elapsed_timer2 >= 3:
                    print(
                        f'3 segundos sem receber o proximo pacote, enviando resposta novamente...')
                    self.send_package()
                    self.timer2 = time.time()

            self.get_header()
            self.get_payload_eop()
            # verify eop and current == last + 1

            # verificar se o pacote atual é igual ao anterior +1
            self.is_next_package = self.n_last_package_received + 1 == self.n_current_package
            self.is_eop_right = self.r_eop == b'\xff\xaa\xff\xaa'

            print(f'Recebeu o proximo? [{self.is_next_package}]', end=' | ')
            print(f'Is eop ok?  [{self.is_eop_right}]', end=" | ")
            print(
                f'Received package [{self.n_current_package} / {self.quantity_packages_to_receive}]')

            self.build_response()
            self.send_package()

        print(f'Received all packages')
        self.juntar_imagem()

    def juntar_imagem(self):
        received_img = b''.join(self.l_received_payloads)

        with open('imagem-recebida.png', 'wb') as file:
            file.write(received_img)

        print(f'Imagem salva...\n')

    def main(self):
        print(f'Servidor inicializado')
        self.server_handshake()
        time.sleep(0.1)
        self.receive_full_packages()

        time.sleep(1)
        self.com2.disable()


if __name__ == '__main__':
    server = Server()
    server.main()
    os._exit(os.EX_OK)
