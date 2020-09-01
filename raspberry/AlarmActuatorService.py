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
import simpleaudio as sa

WINDOW = timedelta(minutes=10)

class AlarmActuatorService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.alarm = 0
        self.alarm_set = False

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''

        self.audio_filename = '../etc/alarm.wav'
        self.wave_obj = sa.WaveObject.from_wave_file(self.audio_filename)
        self.play_obj = None

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/actuators':
            self.alarm = message['start_alarm']
        if topic == self.main_topic + '/config_updates':
            self.updateConfig()
            self.last_update = message

    def alarmStart(self):
        logging.info('alarm started')
        self.play_obj = self.wave_obj.play()

    def alarmStop(self):
        logging.info('alarm stopped')
        self.play_obj.stop()

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        self.alarm_set = config_dict['alarm_set']
        self.main_topic = config_dict['network_name'] + '/' + config_dict['room_name']
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s, alarm_set: %s', self.night_start,
                     self.alarm_time, self.alarm_set)


def runAlarmActuator(myAlarmActuator):
        logging.info(myAlarmActuator.client.mySubscribe(myAlarmActuator.main_topic + '/config_updates'))
        
        while True:
            try:
                if myAlarmActuator.alarm_time and myAlarmActuator.alarm_set:
                    if myAlarmActuator.alarm_time-WINDOW <= datetime.now() <= myAlarmActuator.alarm_time + WINDOW:
                        logging.info(myAlarmActuator.client.mySubscribe(myAlarmActuator.main_topic + '/actuators'))

                        while myAlarmActuator.alarm_time-WINDOW <= datetime.now() < myAlarmActuator.alarm_time+WINDOW:

                            if myAlarmActuator.alarm == 1:
                                myAlarmActuator.alarmStart()
                                while myAlarmActuator.alarm == 1:
                                    time.sleep(1)
                                myAlarmActuator.alarmStop()
                                break
                            time.sleep(1)

                        logging.info(myAlarmActuator.client.myUnsubscribe(myAlarmActuator.main_topic + '/actuators'))
                time.sleep(15)
            except KeyboardInterrupt:
                logging.info(myAlarmActuator.client.stop())


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/alarm_actuator_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']

    # Instantiate and start the alarm actuators
    logging.info('Instantiating the actuators')
    rooms = []

    i = 0
    for dev in devices:
        if 'motion' in dev["sensors"] and 'alarm' in dev["actuators"]:
            url = f'http://{dev["ip"]}:{dev["port"]}'
            id = 'AlarmActuatorService_' + dev["name"] + str(i)
            rooms.append(AlarmActuatorService(id, url, broker_host, broker_port))
            logging.info(rooms[-1].client.start())
            i += 1

    roomThreads = list()
    for room in rooms:
        roomThreads.append(threading.Thread(target=runAlarmActuator, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()

