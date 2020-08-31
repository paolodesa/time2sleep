from etc.MyMQTT import *
import json
from datetime import datetime
import time
import requests
import logging

# The new idea is that of creating an instance of SleepStateService per room, and let it manage
# that room autonomously. Therefore all the logic is moved inside the notify method.

WINDOW = 10

class AlarmSchedulerService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.alarm = 0
        self.sleep_state = ''

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''
        self.main_topic = ''

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.load(payload)
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

    def alarmStop(self):
        msg = json.dumps({'start_alarm': 0})
        self.client.myPublish(self.main_topic + '/actuators', msg)
        self.alarm = 0
        self.sleep_state = 'awake'

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        self.main_topic = config_dict['network'] + '/' + config_dict['room_name']
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s', self.night_start,
                     self.alarm_time)


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/alarm_scheduler_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    logging.info('Connecting to the catalogue...')
    catalogue = requests.get('http://127.0.0.1:8082').json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    devices = catalogue['devices']

    for dev in devices:
        if 'motion' in dev["sensors"] and 'alarm' in dev["actuators"]:
            url = dev["ip"]
            port = dev["port"]
            name = dev["name"]

    rb_url = f'http://{url}:{port}'

    # rb_url = 'http://127.0.0.1:8080'
    # main_topic = 'Time2sleep/bedroom3/'
    # broker_host = '127.0.0.1'
    # broker_port = 1883

    # Instantiate and start the sleep state evaluator
    logging.info('Instantiating the Scheduler')
    myAlarmScheduler = AlarmSchedulerService('SleepStateService', rb_url, broker_host, broker_port)
    logging.info('raspberry_url:%s, main_topic:%s, broker_host:%s, broker_port:%d',
                 rb_url, myAlarmScheduler.main_topic, broker_host, broker_port)
    logging.info(myAlarmScheduler.client.start())

    # Subscribe to config change alert topic
    # TODO: for room in rooms:     mySleepStateEval.client.mySubscribe(main_topic + room + '/config_updates')
    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + 'config_updates'))

    try:
        while True:
            if myAlarmScheduler.alarm_time:
                # Subscribe to motion sensor topic during the night
                if myAlarmScheduler.night_start <= datetime.now() <= myAlarmScheduler.alarm_time + WINDOW:
                    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + 'bed'))
                    logging.info(myAlarmScheduler.client.mySubscribe(myAlarmScheduler.main_topic + 'sleep_state'))

                    while myAlarmScheduler.alarm_time-WINDOW >= datetime.now() > myAlarmScheduler.alarm_time+WINDOW:
                        if myAlarmScheduler.alarm == 0 and myAlarmScheduler.sleep_state == 'light':
                            myAlarmScheduler.alarmStart()
                            inactivity_counter = 0

                        if myAlarmScheduler.alarm == 1 and myAlarmScheduler.sensor_motion == 0:
                            inactivity_counter += 1

                        if (myAlarmScheduler.alarm == 1 and myAlarmScheduler.sensor_motion == 1) or inactivity_counter == 60:
                            myAlarmScheduler.alarmStop()

                        time.sleep(1)

                    logging.info(myAlarmScheduler.client.myUnsubscribe(myAlarmScheduler.main_topic + 'bed'))
                    logging.info(myAlarmScheduler.client.myUnsubscribe(myAlarmScheduler.main_topic + 'sleep_state'))

    except KeyboardInterrupt:
        logging.info(myAlarmScheduler.client.stop())
