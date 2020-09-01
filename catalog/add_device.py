import requests
import socket
import json


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

host = input('Enter the catalog server IP address: ')
catalog_port = input('Enter the catalog port: ')
url = f'http://{host}:{catalog_port}/addDevice'
ip = get_ip_address()
port = 8080
with open('../etc/t2s_conf.json', 'r') as f:
    conf = json.load(f)
    f.close()
name = conf['room_name']
sensors = ['vibration', 'motion', 'noise', 'temperature', 'humidity']
actuators = ['light', 'alarm']
body = {'ip': ip, 'port': port, 'name': name, 'sensors': sensors, 'actuators': actuators}
res = requests.post(url, json.dumps(body))
print(res.text)
