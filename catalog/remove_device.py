import requests
import socket
import json


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

host = input('Enter the catalog server IP address: ')
url = 'http://' + host + ':8080/removeDevice'
ip = get_ip_address()
body = {'ip': ip}
res = requests.post(url, json.dumps(body))
print(res.text)
