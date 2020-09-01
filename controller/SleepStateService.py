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

THRESHOLD = 50
WINDOW = timedelta(minutes=10)

class SleepStateService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.sensor_noise = 0
        self.sensor_vibration = 0
        self.state = "light"
        self.alarm_set = False

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''
        self.alarm_stopped = False

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
            self.updateConfig()
            self.last_update = message

    def evalState(self):
        if self.sensor_motion + self.sensor_noise + self.sensor_vibration > THRESHOLD:
            self.state = 'light'
        else:
            self.state = 'deep'

        msg = json.dumps({'sleep_state': self.state})
        self.client.myPublish(self.main_topic + '/sleep_state', msg)
        logging.debug('STATE: ' + self.state)

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        self.alarm_set = config_dict['alarm_set']
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s, alarm_set: %s', self.night_start,
                     self.alarm_time, self.alarm_set)


def runSleepStateEval(mySleepStateEval):
        logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/config_updates'))

        while True:
            try:
                if mySleepStateEval.alarm_time and mySleepStateEval.alarm_set:
                    # Subscribe to motion sensor topic during the night
                    if mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time + WINDOW:
                        logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/sensors/#'))
                        logging.info(mySleepStateEval.client.mySubscribe(mySleepStateEval.main_topic + '/actuators/alarm'))

                        while mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time + WINDOW:
                            time.sleep(15)
                            if mySleepStateEval.alarm_set == False:
                                break
                            else:
                                mySleepStateEval.evalState()
                            

                        logging.info(mySleepStateEval.client.myUnsubscribe(mySleepStateEval.main_topic + '/sensors/#'))
                        logging.info(mySleepStateEval.client.myUnsubscribe(mySleepStateEval.main_topic + '/actuators/alarm'))
                time.sleep(15)
            except KeyboardInterrupt:
                logging.info(mySleepStateEval.client.stop())


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/sleep_state_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']

    # Instantiate and start the alarm scheduler
    logging.info('Instantiating the Evaluators')
    rooms = []

    i = 0
    for dev in devices:
        if 'motion' in dev["sensors"] and 'noise' in dev["sensors"] and 'vibration' in dev["sensors"]:
            url = f'http://{dev["ip"]}:{dev["port"]}'
            id = 'SleepEvalService_' + dev["name"] + str(i)
            rooms.append(SleepStateService(id, url, broker_host, broker_port))
            logging.info(rooms[-1].client.start())
            i += 1

    # -- Retrieve here the list of services and devices from the catalogue
    # TODO
    # logging.info('Connecting to the catalogue...')
    # rb_url = 'http://127.0.0.1:8080'
    # main_topic = 'Time2sleep/bedroom3/'
    # broker_host = '127.0.0.1'
    # broker_port = 1883

    # logging.info('raspberry_url:%s, main_topic:%s, broker_host:%s, broker_port:%d',
    #              rb_url, main_topic, broker_host, broker_port)

    # # Instantiate and start the sleep state evaluator
    # logging.info('Instantiating the Evaluator')
    # mySleepStateEval = SleepStateService('SleepStateService', rb_url, broker_host, broker_port)
    # logging.info(mySleepStateEval.client.start())

    # Subscribe to config change alert topic
    # TODO: for room in rooms:     mySleepStateEval.client.mySubscribe(main_topic + room + '/config_updates')
    
    roomThreads = list()
    for room in rooms:
        roomThreads.append(threading.Thread(target=runSleepStateEval, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()
    
