import sys
sys.path.insert(0, "../")
from etc.MyMQTT import *
from etc.globalVar import CATALOG_ADDRESS
import json
from datetime import datetime
import requests
import logging
import threading
import time

# The new idea is that of creating an instance of LightControllerService per room, and let it manage
# that room autonomously. Therefore all the logic is moved inside the notify method.

THRESHOLD = 1


class LightControllerService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.light_set = True

        self.sensor_motion = 0
        self.light_on = False
        self.last_update = ''
        self.main_topic = ''

        self.updateConfig()

    def notify(self, topic, payload):
        if topic == self.main_topic + '/sensors/motion':
            message = json.loads(payload)
            self.sensor_motion = message['value']

        # TODO: if topic == main_topic/*/ + 'config_updates': room = topic.parse('/')[1]
        if topic == self.main_topic + '/config_updates':
            self.updateConfig()
            self.last_update = message

    def LightOn(self):
        msg = json.dumps({'value': 1})
        self.client.myPublish(self.main_topic + '/actuators/light', msg)
        self.light_on = True
        logging.debug(self.client.clientID + ': LIGHT ON')

    def LightOff(self):
        msg = json.dumps({'value': 0})
        self.client.myPublish(self.main_topic + '/actuators/light', msg)
        self.light_on = False
        logging.debug(self.client.clientID + ': LIGHT OFF')

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s', self.night_start, self.alarm_time)


def runLightController(myLightController):
    # Subscribe to config change alert topic
    logging.info(myLightController.client.mySubscribe(myLightController.main_topic + '/config_updates'))

    try:
        while True:
            # Subscribe to motion sensor topic during the night
            if (myLightController.night_start <= datetime.now() <= myLightController.alarm_time) and myLightController.light_set:
                logging.info(myLightController.client.mySubscribe(myLightController.main_topic + '/sensors/motion'))

                while (myLightController.night_start <= datetime.now() <= myLightController.alarm_time) and myLightController.light_set:
                    if not myLightController.light_on:
                        ctr = 0
                        if myLightController.sensor_motion >= THRESHOLD:
                            myLightController.LightOn()
                    elif ctr >= 5:
                        if myLightController.sensor_motion < THRESHOLD:
                            myLightController.LightOff()
                    time.sleep(1)
                    ctr += 1

                logging.info(myLightController.client.myUnsubscribe(myLightController.main_topic + '/sensors/motion'))

    except KeyboardInterrupt:
        logging.info(myLightController.client.stop())


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/light_controller_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']

    # Instantiate and start the light controller
    logging.info('Instantiating the controllers')
    rooms = []
    for dev in devices:
        if 'motion' in dev["sensors"] and 'light' in dev["actuators"]:
            url = f'http://{dev["ip"]}:{dev["port"]}'
            id = 'LightControllerService_' + dev["name"]
            rooms.append(LightControllerService(id, url, broker_host, broker_port))
            logging.info(rooms[-1].client.start())

    roomThreads = list()
    for room in rooms:
        roomThreads.append(threading.Thread(target=runLightController, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()

