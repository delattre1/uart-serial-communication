import numpy as np

HEAD = [bytes([0]) for i in range(10)]
PAYLOAD = [bytes([0]) for i in range(0)]
EOP = [bytes([255]) for i in range(4)]

# Quando o cliente enviar um pacote, deve informar obrigatoriamente (em algum espaço do head reservado a isso), o
# número do pacote e o número total de pacotes que serão transmitidos.


def datagram_builder(head=HEAD, payload=PAYLOAD, eop=EOP, current_package=1, total_of_packages=0, server_available=False, acknowledge=False, finished=False, fake_size=False):
    size = len(payload + eop)

    if fake_size:
        size -= 4
    # print(f'\nlist(payload): \n{list(payload)}\n')
    # size += 1  # to raise some error
    head[0] = size.to_bytes(1, 'big')
    byte_current_package = current_package.to_bytes(2, 'big')
    byte_total_of_packages = total_of_packages.to_bytes(2, 'big')

    # to simulate an error
    # if current_package == 7:
    #    byte_current_package = int(8).to_bytes(2, 'big')

    head[1] = byte_current_package[0:1]
    head[2] = byte_current_package[1:2]

    head[3] = byte_total_of_packages[0:1]
    head[4] = byte_total_of_packages[1:2]

    if server_available:  # for handshake
        head[5] = bytes([255])
    #print(f'acknowledge: {acknowledge}')

    if acknowledge == True:
        head[6] = bytes([255])
    else:
        head[6] = bytes([0])

    if finished == True:
        head[7] = bytes([255])

    #print(f'head {head}')
    # print(f'payload {payload}')
    # print(f'eop {eop}')
    pacote = head + payload + eop
    # print(f'\n Pacote:\n {pacote}')
    # print(f'acabei de criar um pacote: {len(pacote)}')
    return np.asarray(pacote)


def receivement_handler(rxBuffer):
    length = len(rxBuffer)
    rx_head = rxBuffer[:10]
    rx_payload = rxBuffer[10:length - 4]
    rx_eop = rxBuffer[length - 4: length]

    return rx_head, rx_payload, rx_eop


def separate_packages(img_array):
    len_img = len(img_array)
    tamanho_pacote = 114
    resto = len_img % tamanho_pacote
    pacotes = [list(img_array[i:i+tamanho_pacote])
               for i in range(0, len_img - resto, tamanho_pacote)]
    pacotes.append(list(img_array[len_img - resto: len_img]))

    pacotes_bytes_list = []
    for i in range(len(pacotes)):
        pacotes_bytes_list.append([])
        for char in pacotes[i]:
            pacotes_bytes_list[i].append(bytes([char]))

    return pacotes_bytes_list


def open_image(path):
    with open(path, "rb") as image:
        f = image.read()
        img_array = bytearray(f)
    return img_array
