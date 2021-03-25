from enlace import *
import os
import time
import numpy as np
from datagram import Datagram
from utils import get_current_time

serialName = "/dev/ttyVirtualS0"

CLIENT_ID = 1
SERVER_ID = 2
FILE_ID = 1


class Server:
    def __init__(self,):
        self.com2 = enlace(serialName)
        self.com2.enable()
        self.l_received_payloads = []
        self.str_log = ''

    def send_package(self):
        pkg = np.asarray(self.package)
        len_pkg = len(pkg)
        self.com2.sendData(pkg)

        head_pkg_bin = list(self.package)[:10]
        head_pkg = [int.from_bytes(byte, 'big') for byte in head_pkg_bin]
        msg_type = head_pkg[0]

        self.append_log(msg_type, len_pkg)

    def append_log(self, msg_type, len_pkg):
        send_or_receive = 'send'

        str_event = f'{get_current_time()} | {send_or_receive}    | {msg_type} | {len_pkg} \n'

        self.str_log += str_event

    def write_logs(self):
        with open('logs/log_server2.txt', 'a') as fd:
            fd.write(self.str_log)

    def get_header(self):
        self.r_header, self.len_r_header = self.com2.getData(10)

    def get_payload_eop(self):
        self.package_header = list(self.r_header)
        package_size = 4
        msg_type = self.package_header[0]
        self.n_of_packages = self.package_header[3]
        self.n_current_package = self.package_header[4]

        # appending to log
        send_or_receive = 'receive'
        total_size_pkg = package_size + 10
        if msg_type == 3:
            str_event = f'{get_current_time()} | {send_or_receive} | {msg_type} | {total_size_pkg} | [{self.n_current_package}/{self.n_of_packages}]\n'
        else:
            str_event = f'{get_current_time()} | {send_or_receive} | {msg_type} | {total_size_pkg} |\n'
        self.str_log += str_event

        if msg_type == 3:
            payload_size = self.package_header[5]
            package_size += payload_size

        if msg_type == 5:
            print(f'Recebido sinal de desligamento da outra parte...')
            print(f'Encerrando o processo')
            self.shutdown()

        self.r_package, self.len_r_package = self.com2.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

    def server_handshake(self):
        is_handshake_successful = False
        while not is_handshake_successful:
            self.get_header()
            self.get_payload_eop()
            self.quantity_packages_to_receive = self.package_header[3]
            print(f'header recebido: {self.r_header}')

            if self.package_header[2] == SERVER_ID:
                print(f'Recebido HS do client - ID correto\n')
                if self.package_header[0] == 1:

                    payload = []
                    header_list = [0 for i in range(10)]
                    header_list[0] = 2  # mensagem to tipo 2 - server ocioso
                    header_list[1] = CLIENT_ID
                    header_list[2] = SERVER_ID

                    datagram_obj = Datagram(payload, header_list)
                    self.package = datagram_obj.get_datagram()
                    self.send_package()
                    is_handshake_successful = True
                    print(f'enviado resposta para o client')

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
            self.timer1 = time.time()
            self.timer2 = self.timer1

            while self.com2.rx.getBufferLen() == 0:
                current_time = time.time()
                elapsed_timer1 = current_time - self.timer1
                elapsed_timer2 = current_time - self.timer2

                if elapsed_timer1 >= 20:
                    print(f'Tempo máximo excedido, avisando client desligamento...')
                    payload = []

                    header_list = [1 for i in range(10)]
                    header_list[0] = 5
                    header_list[1] = CLIENT_ID
                    header_list[2] = SERVER_ID

                    datagram_obj = Datagram(payload, header_list)
                    self.package = datagram_obj.get_datagram()
                    self.send_package()
                    self.shutdown()

                if elapsed_timer2 >= 5:
                    print(
                        f'5 segundos sem receber o proximo pacote, enviando resposta novamente...')
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

        self.shutdown()

    def shutdown(self):
        time.sleep(0.2)
        self.com2.disable()
        self.write_logs()
        os._exit(os.EX_OK)
        print(f'Conexão encerrada')


if __name__ == '__main__':
    server = Server()
    server.main()
