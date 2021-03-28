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
        self.str_log = ''
        self.start_execution_time = 0

    def send_package(self):
        delta_time = time.time() - self.start_execution_time
        if delta_time > 3 and delta_time < 10:  # to simulate and error in the connection
            print('\n')
            print(delta_time)
            print('nao enviei nada pra simular o problema \n')
            pass
        else:
            pkg = np.asarray(self.package)
            self.com1.sendData(pkg)

            send_or_receive = 'send'
            head_pkg_bin = list(self.package)[:10]
            head_pkg = [int.from_bytes(byte, 'big') for byte in head_pkg_bin]

            msg_type = head_pkg[0]
            total_pkgs = head_pkg[3]
            current_pkg = head_pkg[4]

            if msg_type == 3:
                str_event = f'{get_current_time()} | {send_or_receive}    | {msg_type} | {len(pkg)} | [{current_pkg}/{total_pkgs}] | \n'
            else:
                str_event = f'{get_current_time()} | {send_or_receive}    | {msg_type} |\n'
            self.str_log += str_event

    def write_logs(self):
        with open('logs/log_client5.txt', 'a') as fd:
            fd.write(self.str_log)

    def build_packages(self):
        self.header_list = [1 for i in range(10)]
        self.header_list[0] = 3  # mensagem to tipo 1 - handshake
        self.header_list[1] = CLIENT_ID
        self.header_list[2] = SERVER_ID

        for index_package in range(len(self.l_bytes_img)):
            payload = self.l_bytes_img[index_package]
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
            self.shutdown()

        self.n_of_packages = self.package_header[3]
        self.n_of_current_package = self.package_header[4]

        self.r_package, self.len_r_package = self.com1.getData(package_size)
        self.r_payload = self.r_package[:-4]
        self.r_eop = self.r_package[-4:]

        # appending to log
        send_or_receive = 'receive'
        total_size_pkg = package_size + 10
        str_event = f'{get_current_time()} | {send_or_receive} | {msg_type} | {total_size_pkg}\n'
        self.str_log += str_event

    def client_handshake(self):
        handshake_successful = False
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

        self.start_time1 = time.time()
        self.start_time2 = time.time()
        while not handshake_successful:
            while self.com1.rx.getBufferLen() == 0:
                self.time_delta1 = time.time() - self.start_time1
                self.time_delta2 = time.time() - self.start_time2
                if self.time_delta2 > 20:
                    print(f'Tempo máximo excedido, avisando server desligamento...')
                    self.create_shut_down_signal()
                    self.send_package()
                    time.sleep(1)
                    self.shutdown()

                elif self.time_delta1 >= 5:
                    should_send_again = input(
                        'Didn\'t receive response. Send again? (s/n) ')
                    if should_send_again == 's':
                        print(f'Enviando novamente...\n')
                        self.send_package()
                        self.start_time1 = time.time()
                    else:
                        self.shutdown()

            self.get_header()
            self.get_payload_eop()
            if self.package_header[0] == 2:
                handshake_successful = True
                print(f'Server está ocioso... começando o envio\n')
            else:
                print(f'Não teve sucesso no handshake...')

    def send_full_packages(self):
        index = 0
        for index_package in range(self.len_packages):
            self.package = self.l_packages[index_package]
            self.send_package()
            self.timer1 = time.time()
            self.timer2 = self.timer1
            print(f'Enviando o pacote [{index_package + 1}]...')
            last_sent_pkg = index_package + 1
            self.verify_server_receivement(last_sent_pkg)

    def simulate_error(self, index_package):
        pkg_correto = self.package
        self.package = self.l_packages[index_package+2]
        self.send_package()
        self.package = pkg_correto
        print(f'Enviei o pacote errado para simular erro')

    def create_shut_down_signal(self):
        payload = []
        self.header_list = [1 for i in range(10)]
        self.header_list[0] = 5  # mensagem to tipo 1 - handshake
        self.header_list[1] = CLIENT_ID
        self.header_list[2] = SERVER_ID

        datagram_obj = Datagram(payload, self.header_list)
        self.package = datagram_obj.get_datagram()

    def verify_server_receivement(self, last_sent_pkg):
        msg_type = ''
        last_successful_msg = ''
        while msg_type != 4 or last_successful_msg != last_sent_pkg:

            # loops until notice something in the buffer, then verify
            while self.com1.rx.getBufferLen() == 0:
                current_time = time.time()
                elapsed_timer1 = current_time - self.timer1
                elapsed_timer2 = current_time - self.timer2

                if elapsed_timer1 >= 20:
                    print(f'Tempo máximo excedido, avisando server desligamento...')
                    self.create_shut_down_signal()
                    self.send_package()
                    time.sleep(1)
                    self.shutdown()
                if elapsed_timer2 >= 5:
                    print(f'5 segundos sem resposta, enviando novamente...')
                    self.send_package()
                    self.timer2 = time.time()

            self.get_header()
            self.get_payload_eop()
            msg_type = self.package_header[0]
            last_successful_msg = self.package_header[7]
            print(
                f'Tipo msg: {msg_type} | última com sucesso: {last_successful_msg}')

            if msg_type == 4:
                print(f'Server recebeu corretamente o pacote. Enviando o próximo')

            elif msg_type == 6:
                required_pkg = self.package_header[6] - 1
                print(
                    f'Server nao recebeu corretamente. Solicitou o {required_pkg}...')
                self.package = self.l_packages[required_pkg]
                self.send_package()
                self.timer2 = time.time()

    def main(self):
        self.build_packages()

        self.client_handshake()

        self.start_execution_time = time.time()

        self.send_full_packages()
        time.sleep(0.5)

        execution_time = time.time() - self.start_execution_time
        print(f'Tempo total de execução: {execution_time: .2f}')
        #print(f'Velocidade: {len(COLOCAR_TOTAL_BYTES)/execution_time:.2f} B/s')
        self.shutdown()

    def shutdown(self):
        time.sleep(1)
        self.com1.disable()
        self.write_logs()
        os._exit(os.EX_OK)
        print(f'Conexão encerrada')


if __name__ == '__main__':
    client = Client('imgs/advice.png')
    client.main()
