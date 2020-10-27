#!/usr/bin/env python3
import sys

sys.path.insert(0, "../")
from etc.MyMQTT import *
import json
import time
import requests
from datetime import datetime as dt
from etc.globalVar import CATALOG_ADDRESS


class LocalSubscriber:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.vibration = []
        self.noise = []
        self.motion = []
        self.temperature = []
        self.humidity = []
        self.sleepState = []

    def notify(self, msg_topic, msg_payload):
        payload = json.loads(msg_payload)
        # print(msg_topic, '  --  ', payload)
        if msg_topic == local_topic + '/sensors/vibration':
            self.vibration.append(payload['value'])

        elif msg_topic == local_topic + '/sensors/noise':
            self.noise.append(payload['value'])

        elif msg_topic == local_topic + '/sensors/motion':
            self.motion.append(payload['value'])

        elif msg_topic == local_topic + '/sensors/temperature':
            self.temperature.append(payload['value'])

        elif msg_topic == local_topic + '/sensors/humidity':
            self.humidity.append(payload['value'])

        elif msg_topic == local_topic + '/sleep_state':
            if payload['sleep_state'] == 'light':
                self.sleepState.append(1)
            elif payload['sleep_state'] == 'awake':
                self.sleepState = None
            else:
                self.sleepState.append(0)


def average(num_list):
    return round(sum(num_list) / len(num_list), 0)


catalogue = requests.get(CATALOG_ADDRESS).json()
broker_host = catalogue['broker_host']
broker_port = catalogue['broker_port']
with open('../etc/t2s_conf.json', 'r') as f:
    config_dict = json.load(f)
    local_topic = config_dict['network_name'] + '/' + config_dict['room_name']

local_client = LocalSubscriber('local', broker_host, broker_port)
local_client.client.start()
local_client.client.mySubscribe(local_topic + '/#')
while True:
    try:
        if (local_client.vibration != [] and local_client.noise != [] and local_client.motion != [] and
                local_client.temperature != [] and local_client.humidity != []):
            if (local_client.sleepState != []):
                try:
                    requests.get(f'https://api.thingspeak.com/update.json?api_key=AAN3J152MUTN1YYX'
                                 f'&field1={average(local_client.vibration)}'
                                 f'&field2={average(local_client.noise)}'
                                 f'&field3={average(local_client.motion)}'
                                 f'&field4={average(local_client.temperature)}'
                                 f'&field5={average(local_client.humidity)}'
                                 f'&field6={average(local_client.sleepState)}')
                    local_client.vibration = []
                    local_client.noise = []
                    local_client.motion = []
                    local_client.temperature = []
                    local_client.humidity = []
                    local_client.sleepState = []

                    print(dt.now(), ' - data pushed to TS')
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
