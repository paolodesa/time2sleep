#!/usr/bin/env python3

import json
import time
from MyMQTT import *


class TSPublisher():
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)


class LocalSubscriber():
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
    def notify(self, msg_topic, msg_payload):
        payload = json.loads(msg_payload)
        if msg_topic == local_topic + '/vibration':
            vibration = str(payload['value'])
        elif msg_topic == local_topic + '/noise':
            noise = str(payload['value'])
        elif msg_topic == local_topic + '/motion':
            motion = str(payload['value'])
        elif msg_topic == local_topic + '/temperature':
            temperature = str(payload['value'])
        elif msg_topic == local_topic + '/humidity':
            humidity = str(payload['value'])
        ts_topic = 'channels/1127842/publish/AAN3J152MUTN1YYX'
        ts_client = TSPublisher('ts', 'mqtt.thingspeak.com', 1883).client
        ts_client.start()
        ts_payload = 'field1=' + vibration + '&field2=' + noise + '&field3=' + motion + '&field4=' + temperature + '&field5=' + humidity
        ts_client.myPublish(ts_topic, ts_payload)
        ts_client.stop()


local_topic = 'Time2sleep/bedroom1/sensors'
local_client = LocalSubscriber('local', '127.0.0.1', 1883).client
local_client.start()
local_client.mySubscribe(local_topic + '/#')
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        local_client.stop()
        exit()
    

        


