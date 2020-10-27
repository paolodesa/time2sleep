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

WINDOW = timedelta(minutes=10)
DEVICES = []


class AlarmSchedulerService:
    def __init__(self, clientID, room_name, rb_url, broker_host, broker_port):
        # Private attributes
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.id = room_name
        self.rb_url = rb_url
        self.main_topic = ''
        # Subscriptions
        self.sensor_motion = 0
        self.sleep_state = ''
        # Settings
        self.alarm_set = False
        self.adaptive_alarm = False
        self.alarm_time = 0
        self.last_update = ''
        # Decision variable
        self.alarm = 0

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/sensors/motion':
            self.sensor_motion = message['value']

        if topic == self.main_topic + '/sleep_state':
            self.sleep_state = message['sleep_state']

        if topic == self.main_topic + '/config_updates':
            self.updateConfig()
            self.last_update = message['timestamp']

    def alarmStart(self):
        msg = json.dumps({'value': 1})
        self.client.myPublish(self.main_topic + '/actuators/alarm', msg)
        self.alarm = 1
        logging.info('alarm started')
        time.sleep(3)

    def alarmStop(self):
        msg = json.dumps({'value': 0})
        self.client.myPublish(self.main_topic + '/actuators/alarm', msg)
        self.alarm = 0
        logging.info('alarm stopped')

        self.sleep_state = 'awake'
        msg = json.dumps({'sleep_state': 'awake'})
        self.client.myPublish(self.main_topic + '/sleep_state', msg)

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        msg = json.dumps({'sleep_state': 'awake'})
        self.client.myPublish(self.main_topic + '/sleep_state', msg)
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%Y,%m,%d,%H,%M')
        self.alarm_set = config_dict['alarm_set']
        self.adaptive_alarm = config_dict['adaptive_alarm']
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        logging.info(self.client.clientID + ' CONFIG - alarm_time: %s, alarm_set: %s, adaptive_alarm: %s',
                     self.alarm_time, self.alarm_set, self.adaptive_alarm)

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
            if dev['name'] not in ids and 'motion' in dev["sensors"] and 'alarm' in dev["actuators"]:
                url = f'http://{dev["ip"]}:{dev["port"]}'
                id = 'AlarmSchedulerService_' + dev["name"]
                room_name = dev['name']
                new_rooms.append(AlarmSchedulerService(id, room_name, url, broker_host, broker_port))
                logging.info(new_rooms[-1].client.start())
        DEVICES = devices
        newRoomThreads = list()
        for room in new_rooms:
            newRoomThreads.append(threading.Thread(target=runAlarmScheduler, args=(room,)))
        for roomThread in newRoomThreads:
            roomThread.start()
        time.sleep(5)


def runAlarmScheduler(myAlarmScheduler):
    # Subscribe to config change alert topic
    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/config_updates'))
    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/sensors/motion'))
    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/sleep_state'))

    while myAlarmScheduler.isActive():
        try:
            if myAlarmScheduler.alarm_set:
                # Subscribe to motion sensor topic during the night
                time_delta = WINDOW if myAlarmScheduler.adaptive_alarm else timedelta(seconds=30)

                while myAlarmScheduler.alarm_time - time_delta <= datetime.now() < myAlarmScheduler.alarm_time + time_delta and myAlarmScheduler.isActive():
                    if (myAlarmScheduler.alarm == 0 and myAlarmScheduler.sleep_state == 'light') or datetime.now() >= myAlarmScheduler.alarm_time:
                        myAlarmScheduler.alarmStart()
                        break

                while myAlarmScheduler.alarm == 1:
                    if myAlarmScheduler.sensor_motion or datetime.now() - myAlarmScheduler.alarm_time > timedelta(seconds=60):
                        myAlarmScheduler.alarmStop()

            time.sleep(15)
        except KeyboardInterrupt:
            logging.info(myAlarmScheduler.client.stop())

    logging.info(myAlarmScheduler.client.stop())


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/alarm_scheduler_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']
    DEVICES = devices

    # Instantiate and start the alarm schedulers
    logging.info('Instantiating the schedulers')
    rooms = []

    for dev in devices:
        room_url = f'http://{dev["ip"]}:{dev["port"]}'
        room_id = 'AlarmSchedulerService_' + dev["name"]
        rooms.append(AlarmSchedulerService(room_id, dev["name"], room_url, broker_host, broker_port))
        logging.info(rooms[-1].client.start())

    roomThreads = []
    for room in rooms:
        roomThreads.append(threading.Thread(target=runAlarmScheduler, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()

    checkNewDevicesThread = threading.Thread(target=checkNewDevices)
    checkNewDevicesThread.start()
