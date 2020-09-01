from MyMQTT import *
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

class AlarmSchedulerService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.alarm = 0
        self.sleep_state = ''
        self.alarm_set = False

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/sensors/motion':
            self.sensor_motion = message['value']

        if topic == self.main_topic + '/sleep_state':
            self.sleep_state = message['sleep_state']

        # TODO: if topic == self.main_topic/*/ + 'config_updates': room = topic.parse('/')[1]
        if topic == self.main_topic + '/config_updates':
            self.updateConfig()
            self.last_update = message

    def alarmStart(self):
        msg = json.dumps({'start_alarm': 1})
        self.client.myPublish(self.main_topic + '/actuators', msg)
        self.alarm = 1
        logging.info('alarm started')
        time.sleep(3)

    def alarmStop(self):
        msg = json.dumps({'start_alarm': 0})
        self.client.myPublish(self.main_topic + '/actuators', msg)
        self.alarm = 0
        self.sleep_state = 'awake'
        msg = json.dumps({'sleep_state': 'awake'})
        self.client.myPublish(self.main_topic + '/sleep_state', msg)
        new_night_start = datetime.strftime(self.night_start + timedelta(days=1), '%y,%m,%d,%H,%M')
        new_alarm_time = datetime.strftime(self.alarm_time + timedelta(days=1), '%y,%m,%d,%H,%M')
        config_update = {'night_start': new_night_start, 'alarm_time': new_alarm_time, 'alarm_set': False}
        logging.info(requests.post(self.rb_url + '/changeConfig', json.dumps(config_update)))
        logging.info('alarm stopped')

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


def runAlarmScheduler(myAlarmScheduler):
        logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/config_updates'))
        
        while True:
            try:
                if myAlarmScheduler.alarm_time and myAlarmScheduler.alarm_set:
                    # Subscribe to motion sensor topic during the night
                    if myAlarmScheduler.night_start <= datetime.now() <= myAlarmScheduler.alarm_time + WINDOW:
                        logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/sensors/#'))
                        logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + '/sleep_state'))
                        inactivity_counter = 0

                        while myAlarmScheduler.alarm_time-WINDOW <= datetime.now() < myAlarmScheduler.alarm_time+WINDOW:
                            if (myAlarmScheduler.alarm == 0 and myAlarmScheduler.sleep_state == 'light') or datetime.now() >= myAlarmScheduler.alarm_time+WINDOW-timedelta(minutes=1):
                                myAlarmScheduler.alarmStart()

                            if myAlarmScheduler.alarm == 1 and myAlarmScheduler.sensor_motion == 0:
                                inactivity_counter += 1

                            if (myAlarmScheduler.alarm == 1 and myAlarmScheduler.sensor_motion == 1) or inactivity_counter == 60:
                                myAlarmScheduler.alarmStop()
                                break

                            time.sleep(1)

                        logging.info(myAlarmScheduler.client.myUnsubscribe(myAlarmScheduler.main_topic + '/sensors/#'))
                        logging.info(myAlarmScheduler.client.myUnsubscribe(myAlarmScheduler.main_topic + '/sleep_state'))
                time.sleep(15)
            except KeyboardInterrupt:
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

    # Instantiate and start the alarm scheduler
    logging.info('Instantiating the schedulers')
    rooms = []

    i = 0
    for dev in devices:
        if 'motion' in dev["sensors"] and 'alarm' in dev["actuators"]:
            url = f'http://{dev["ip"]}:{dev["port"]}'
            id = 'AlarmSchedulerService_' + dev["name"] + str(i)
            rooms.append(AlarmSchedulerService(id, url, broker_host, broker_port))
            logging.info(rooms[-1].client.start())
            i += 1

    # rb_url = 'http://127.0.0.1:8080'
    # main_topic = 'Time2sleep/bedroom3/'
    # broker_host = '127.0.0.1'
    # broker_port = 1883

    # Instantiate and start the sleep state evaluator
    # logging.info('Instantiating the Scheduler')
    # myAlarmScheduler = AlarmSchedulerService('SleepStateService', rb_url, broker_host, broker_port)
    # logging.info('raspberry_url:%s, main_topic:%s, broker_host:%s, broker_port:%d',
    #              rb_url, myAlarmScheduler.main_topic, broker_host, broker_port)
    # logging.info(myAlarmScheduler.client.start())

    # Subscribe to config change alert topic
    # TODO: for room in rooms:     mySleepStateEval.client.mySubscribe(main_topic + room + '/config_updates')

    roomThreads = list()
    for room in rooms:
        roomThreads.append(threading.Thread(target=runAlarmScheduler, args=(room,)))

    for roomThread in roomThreads:
        roomThread.start()
