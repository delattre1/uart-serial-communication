from utils import open_image, separate_packages
from datagram import Datagram

img = open_image('imgs/advice.png')
pkgs = separate_packages(img)

for i in pkgs:
    header_list = [1 for i in range(10)]
    a = Datagram(payload=[], header_list=header_list).get_datagram()
    print(a)
    break
