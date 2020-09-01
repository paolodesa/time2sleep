# I consider this script to run on the raspberry where also the config file is stored, so it won't be necessary
# to retrieve it. The catalogue will be reached anyway to retrieve the broker end points.

from etc.MyMQTT import *
from etc.globalVar import CATALOG_ADDRESS
import json
from datetime import datetime
import time
import random
import requests

if __name__ == '__main__':
    with open('../etc/t2s_conf.json', 'r') as f:
        t2s_conf = json.load(f)
        network = t2s_conf['network_name']
        room = t2s_conf['room_name']
        night_start = t2s_conf['night_start']

    main_topic = network + '/' + room

    # FROM CATALOGUE RETRIEVE BROKER_HOST AND PORT
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']

    temperature = 0
    humidity = 0
    vibration = 0
    motion = 0
    noise = 0

    DataPublisher = MyMQTT(main_topic, broker_host, broker_port)
    DataPublisher.start()

    while True:
        try:
            temperature = random.randint(10, 30)
            humidity = random.randint(50, 90)
            vibration = random.randint(0, 100)
            motion = random.randint(0, 1)
            noise = random.randint(20, 90)

            # Publishing Data
            time_instant = datetime.now()
            DataPublisher.myPublish(main_topic + '/sensors/temperature', json.dumps({
                'value': temperature,
                'timestamp': str(time_instant)
            }))
            DataPublisher.myPublish(main_topic + '/sensors/humidity', json.dumps({
                'value': humidity,
                'timestamp': str(time_instant)
            }))
            DataPublisher.myPublish(main_topic + '/sensors/vibration', json.dumps({
                'value': vibration,
                'timestamp': str(time_instant)
            }))
            DataPublisher.myPublish(main_topic + '/sensors/motion', json.dumps({
                'value': motion,
                'timestamp': str(time_instant)
            }))
            DataPublisher.myPublish(main_topic + '/sensors/noise', json.dumps({
                'value': noise,
                'timestamp': str(time_instant)
            }))

            time.sleep(1)

        except KeyboardInterrupt:
            break
