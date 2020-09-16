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
        self.sleepState = None

    def notify(self, msg_topic, msg_payload):
        payload = json.loads(msg_payload)
        if msg_topic == local_topic + '/sensors/vibration':
            self.vibration = str(payload['value'])

        elif msg_topic == local_topic + '/sensors/noise':
            self.noise = str(payload['value'])

        elif msg_topic == local_topic + '/sensors/motion':
            self.motion = str(payload['value'])

        elif msg_topic == local_topic + '/sensors/temperature':
            self.temperature = str(payload['value'])

        elif msg_topic == local_topic + '/sensors/humidity':
            self.humidity = str(payload['value'])

        elif msg_topic == local_topic + '/sleep_state':
            if payload['sleep_state'] == 'light':
                self.sleepState = '1'
            elif payload['sleep_state'] == 'awake':
                self.sleepState = None
            else:
                self.sleepState = '0'


local_topic = 'time2sleep/Bedroom'
local_client = LocalSubscriber('local', '127.0.0.1', 1883)
local_client.client.start()
local_client.client.mySubscribe(local_topic + '/#')
while True:
    try:
        if (local_client.vibration != None and local_client.noise != None and local_client.motion != None and
                local_client.temperature != None and local_client.humidity != None):
            if (local_client.sleepState != None):
                try:
                    requests.get(f'https://api.thingspeak.com/update.json?api_key=AAN3J152MUTN1YYX'
                                f'&field1={local_client.vibration}'
                                f'&field2={local_client.noise}'
                                f'&field3={local_client.motion}'
                                f'&field4={local_client.temperature}'
                                f'&field5={local_client.humidity}'
                                f'&field6={local_client.sleepState}')
                except requests.ConnectionError:
                    time.sleep(5)
                    continue
            else:
                try:
                    requests.get(f'https://api.thingspeak.com/update.json?api_key=AAN3J152MUTN1YYX'
                                 f'&field4={local_client.temperature}'
                                 f'&field5={local_client.humidity}')
                except requests.ConnectionError:
                    time.sleep(5)
                    continue
        time.sleep(15)
    except KeyboardInterrupt:
        local_client.client.stop()
        exit()
