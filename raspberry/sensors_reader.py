# I consider this script to run on the raspberry where also the config file is stored, so it won't be necessary
# to retrieve it. The catalogue will be reached anyway to retrieve the broker end points.

import sys

sys.path.insert(0, "../")
from etc.MyMQTT import *
from etc.globalVar import CATALOG_ADDRESS
import json
from datetime import datetime
import time
import random
import requests
# import RPi.GPIO as GPIO
# import etc.Freenove_DHT as DHT
# import pyaudio
import numpy as np

CHUNK = 2 ** 11
RATE = 44100

motionSensorPin = 11
DHTPin = 7


# def setup():
    # print('Sensors are starting')
    # GPIO.setmode(GPIO.BOARD)
    # GPIO.setup(motionSensorPin, GPIO.IN)
    # GPIO.setup(vibrationSensorPin, GPIO.IN)


if __name__ == '__main__':
    # setup()
    # dht = DHT.DHT(DHTPin)
    # p = pyaudio.PyAudio()
    # stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
    #                 frames_per_buffer=CHUNK)

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

    DataPublisher = MyMQTT(main_topic, broker_host, broker_port, None)
    DataPublisher.start()

    # Simulation of sensors data for debugging
    last_t = random.randint(18, 28)
    last_hum = random.randint(40, 80)
    last_noise = random.randint(10, 20)
    c = -1

    while True:
        c += 1
        try:
            # Simulation of sensors data for debugging
            temperature = int(random.gauss(last_t, 1))
            humidity = int(random.gauss(last_hum, 1))
            vibration = random.randint(0, 1) if c <= 120 or c >= 480 else 0
            motion = 1 if c <= 30 or c >= 560 else 0
            noise = int(random.gauss(last_noise, 2))
            last_t = 18 if temperature < 18 else 28 if temperature > 28 else temperature
            last_hum = 40 if humidity < 40 else 80 if humidity > 80 else humidity
            last_noise = 10 if noise < 10 else 15 if noise > 20 else noise

            # if GPIO.input(motionSensorPin) == GPIO.HIGH:
            #     motion = 1
            # else:
            #     motion = 0

            # if GPIO.input(vibrationSensorPin) == GPIO.HIGH:
            #     vibration = 1
            # else:
            #     vibration= 0

            # chk = dht.readDHT11()
            # if chk is dht.DHTLIB_OK:
            #     temperature = dht.temperature
            #     humidity = dht.humidity
            #
            # data = np.fromstring(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
            # peak = np.average(np.abs(data)) * 2
            # noise = peak

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

    GPIO.cleanup()

    stream.stop_stream()
    stream.close()
    p.terminate()
