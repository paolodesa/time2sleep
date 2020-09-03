#!/usr/bin/env python3
import sys
sys.path.insert(0, "../")
from etc.MyMQTT import *
import json
import time
import requests


class LocalSubscriber():
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.vibration = None
        self.noise = None
        self.motion = None
        self.temperature = None
        self.humidity = None

    def notify(self, msg_topic, msg_payload):
        payload = json.loads(msg_payload)
        if msg_topic == local_topic + '/vibration':
            self.vibration = str(payload['value'])

        elif msg_topic == local_topic + '/noise':
            self.noise = str(payload['value'])

        elif msg_topic == local_topic + '/motion':
            self.motion = str(payload['value'])

        elif msg_topic == local_topic + '/temperature':
            self.temperature = str(payload['value'])

        elif msg_topic == local_topic + '/humidity':
            self.humidity = str(payload['value'])


local_topic = 'time2sleep/bedroom/sensors'
local_client = LocalSubscriber('local', '127.0.0.1', 1883)
local_client.client.start()
local_client.client.mySubscribe(local_topic + '/#')
while True:
    try:
        if (local_client.vibration != None and local_client.noise != None and local_client.motion != None and
                local_client.temperature != None and local_client.humidity != None):
            requests.get(f'https://api.thingspeak.com/update.json?api_key=AAN3J152MUTN1YYX'
                         f'&field1={local_client.vibration}'
                         f'&field2={local_client.noise}'
                         f'&field3={local_client.motion}'
                         f'&field4={local_client.temperature}'
                         f'&field5={local_client.humidity}')

        time.sleep(15)
    except KeyboardInterrupt:
        local_client.client.stop()
        exit()
