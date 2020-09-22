import sys
sys.path.insert(0, "../")
from etc.MyMQTT import *
from etc.globalVar import CATALOG_ADDRESS
import json
from datetime import datetime, timedelta
import time
import requests
import logging
import threading
import RPi.GPIO as GPIO

WINDOW = timedelta(minutes=10)

ledPin = 12

def setup():
    print('GPIO pins setup running...')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(ledPin, GPIO.OUT)

class LightActuatorService:
    def __init__(self, clientID, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.id = clientID
        self.night_start = 0
        self.alarm_set = False
        self.light_set = True
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''
        self.light = 0
        self.lightON = False

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/actuators/light':
            self.light = message['value']
        if topic == self.main_topic + '/config_updates':
            self.updateConfig()
            self.last_update = message

    def lightStart(self):
        if not self.lightON:
            logging.info(self.id + ': Light turned on')
            # Give high voltage to proper GPIO
            GPIO.output(ledPin, GPIO.HIGH)
            self.lightON = True

    def lightStop(self):
        if self.lightON:
            logging.info(self.id + ': Light turned off')
            # Give low voltage to proper GPIO
            GPIO.output(ledPin, GPIO.LOW)
            self.lightON = False

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        with open('../etc/t2s_conf.json', 'r') as f:
            config_dict = json.load(f)

        self.night_start = datetime.strptime(config_dict['night_start'], '%Y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%Y,%m,%d,%H,%M')
        self.alarm_set = config_dict['alarm_set']
        self.light_set = config_dict['light_set']
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s, alarm_set: %s', self.night_start,
                     self.alarm_time, self.alarm_set)


if __name__ == '__main__':
    setup()
    logging.basicConfig(filename='../logs/light_actuator_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']

    # Instantiate and start the light actuators
    with open('../etc/t2s_conf.json', 'r') as f:
            config_dict = json.load(f)
            f.close()

    logging.info('Instantiating the actuator')
    myLightActuator = LightActuatorService('LightActuatorService_' + config_dict['room_name'], broker_host, broker_port)
    logging.info(myLightActuator.client.start())

    logging.info(myLightActuator.client.mySubscribe(myLightActuator.main_topic + '/config_updates'))
    logging.info(myLightActuator.client.mySubscribe(myLightActuator.main_topic + '/actuators/light'))
    while True:
        try:
            if myLightActuator.light == 1:
                myLightActuator.lightStart()
            else:
                myLightActuator.lightStop()

        except KeyboardInterrupt:
            logging.info(myLightActuator.client.stop())
            GPIO.cleanup()
