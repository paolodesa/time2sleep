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

# The new idea is that of creating an instance of SleepStateService per room, and let it manage
# that room autonomously. Therefore all the logic is moved inside the notify method.

THRESHOLD = 1
WINDOW = timedelta(minutes=10)
DEVICES = []


class SleepStateService:
    def __init__(self, clientID, room_name, rb_url, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.id = room_name
        self.sensor_motion = 0
        self.sensor_noise = 0
        self.sensor_vibration = 0
        self.state = "light"
        self.alarm_set = False
        self.night_monitoring = False
        self.adaptive_alarm = False

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''
        self.alarm_stopped = False
        self.counter = 0

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/sensors/motion':
            self.sensor_motion = message['value']

        if topic == self.main_topic + '/sensors/noise':
            self.sensor_noise = message['value']

        if topic == self.main_topic + '/sensors/vibration':
            self.sensor_vibration = message['value']

        if topic == self.main_topic + '/actuators/alarm':
            if message['value'] == 0:
                self.alarm_stopped = True

        # TODO: if topic == self.main_topic/*/ + 'config_updates': room = topic.parse('/')[1]
        if topic == self.main_topic + '/config_updates':
            print(datetime.now(), ' : Config update')
            self.updateConfig()
            self.last_update = message

    def evalState(self):
        if self.sensor_motion + self.sensor_vibration >= THRESHOLD:
            self.state = 'light'
            self.counter = 0
        elif self.sensor_motion + self.sensor_vibration < THRESHOLD:
            self.counter += 1
            if self.counter > 60:
                self.state = 'deep'
            else:
                self.state = 'light'


        msg = json.dumps({'sleep_state': self.state})
        self.client.myPublish(self.main_topic + '/sleep_state', msg)
        logging.debug('STATE: ' + self.state)

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%Y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%Y,%m,%d,%H,%M')
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        self.alarm_set = config_dict['alarm_set']
        self.night_monitoring = config_dict['night_monitoring']
        self.adaptive_alarm = config_dict['adaptive_alarm']
        logging.info(
            self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s, alarm_set: %s, night_monitoring: %s, adaptive_alarm: %s',
            self.night_start,
            self.alarm_time, self.alarm_set, self.night_monitoring, self.adaptive_alarm)

    def isActive(self):
        global DEVICES
        ids = []
        for DEV in DEVICES:
            ids.append(DEV['name'])
        if self.id in ids:
            return True
        else:
            return False


def checkNewDevices():
    while True:
        global DEVICES
        new_rooms = []
        ids = []
        catalogue = requests.get(CATALOG_ADDRESS).json()
        broker_host = catalogue['broker_host']
        broker_port = catalogue['broker_port']
        devices = catalogue['devices']
        for DEV in DEVICES:
            ids.append(DEV['name'])
        for dev in devices:
            if dev['name'] not in ids and 'motion' in dev["sensors"] and 'noise' in dev["sensors"] and 'vibration' in \
                    dev["sensors"]:
                url = f'http://{dev["ip"]}:{dev["port"]}'
                id = 'SleepEvalService_' + dev["name"]
                room_name = dev['name']
                new_rooms.append(SleepStateService(id, room_name, url, broker_host, broker_port))
                logging.info(new_rooms[-1].client.start())
        DEVICES = devices
        newRoomThreads = list()
        for room in new_rooms:
            newRoomThreads.append(threading.Thread(target=runSleepStateEval, args=(room,)))
        for roomThread in newRoomThreads:
            roomThread.start()
        time.sleep(5)


def runSleepStateEval(mySleepStateEval):
    logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/config_updates'))

    while mySleepStateEval.isActive():
        try:
            if mySleepStateEval.alarm_set and mySleepStateEval.night_monitoring:
                # Subscribe to motion sensor topic during the night
                time_delta = WINDOW if mySleepStateEval.adaptive_alarm else timedelta(seconds=30)
                if mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time + time_delta:
                    logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/sensors/#'))
                    logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/actuators/alarm'))

                    while mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time + time_delta and mySleepStateEval.isActive():
                        time.sleep(1)
                        if mySleepStateEval.alarm_stopped == True:
                            mySleepStateEval.alarm_stopped = False
                            break
                        else:
                            mySleepStateEval.evalState()

                    logging.info(mySleepStateEval.client.myUnsubscribe(mySleepStateEval.main_topic + '/sensors/#'))
                    logging.info(
                        mySleepStateEval.client.myUnsubscribe(mySleepStateEval.main_topic + '/actuators/alarm'))
            time.sleep(15)
        except KeyboardInterrupt:
            logging.info(mySleepStateEval.client.stop())

    logging.info(mySleepStateEval.client.stop())


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/sleep_state_service.log', filemode='w', level=logging.INFO,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']
    DEVICES = devices

    # Instantiate and start the alarm scheduler
    logging.info('Instantiating the Evaluators')
    rooms = []

    i = 0
    for dev in devices:
        if 'motion' in dev["sensors"] and 'noise' in dev["sensors"] and 'vibration' in dev["sensors"]:
            url = f'http://{dev["ip"]}:{dev["port"]}'
            id = 'SleepEvalService_' + dev["name"] + str(i)
            room_name = dev['name']
            rooms.append(SleepStateService(id, room_name, url, broker_host, broker_port))
            logging.info(rooms[-1].client.start())
            i += 1

    roomThreads = list()
    for room in rooms:
        roomThreads.append(threading.Thread(target=runSleepStateEval, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()

    checkNewDevicesThread = threading.Thread(target=checkNewDevices)
    checkNewDevicesThread.start()
