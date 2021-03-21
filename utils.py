from datetime import datetime


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


def get_current_time():
    # dd/mm/YY H:M:S
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]
    return dt_string
