from etc.MyMQTT import *
import json
from datetime import datetime
import time
import requests
import logging

# The new idea is that of creating an instance of SleepStateService per room, and let it manage
# that room autonomously. Therefore all the logic is moved inside the notify method.

THRESHOLD = 100


class SleepStateService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.sensor_noise = 0
        self.sensor_vibration = 0
        self.state = "light"

        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0
        self.last_update = ''

        self.updateConfig()

    def notify(self, topic, payload):
        message = json.load(payload)
        if topic == main_topic + 'bed/motion_sensor':
            self.sensor_motion = message['data'][0]['value']

        if topic == main_topic + 'bed/noise_sensor':
            self.sensor_noise = message['data'][0]['value']

        if topic == main_topic + 'bed/vibration_sensor':
            self.sensor_vibration = message['data'][0]['value']

        # TODO: if topic == main_topic/*/ + 'config_updates': room = topic.parse('/')[1]
        if topic == main_topic + 'config_updates':
            self.updateConfig()
            self.last_update = message

    def evalState(self):
        if self.sensor_motion + self.sensor_noise + self.sensor_vibration > THRESHOLD:
            self.state = 'light'
        else:
            self.state = 'deep'

        msg = json.dumps({'sleep_state': self.state})
        self.client.myPublish(main_topic + '/sleep_state', msg)
        logging.debug('STATE: ' + self.state)

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s', self.night_start,
                     self.alarm_time)


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/sleep_state_service.log', filemode='w', level=logging.DEBUG,
                        format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    logging.info('Simulation started')

    # -- Retrieve here the list of services and devices from the catalogue
    # TODO
    logging.info('Connecting to the catalogue...')
    rb_url = 'http://127.0.0.1:8080'
    main_topic = 'Time2sleep/bedroom3/'
    broker_host = '127.0.0.1'
    broker_port = 1883

    logging.info('raspberry_url:%s, main_topic:%s, broker_host:%s, broker_port:%d',
                 rb_url, main_topic, broker_host, broker_port)

    # Instantiate and start the sleep state evaluator
    logging.info('Instantiating the Evaluator')
    mySleepStateEval = SleepStateService('SleepStateService', rb_url, broker_host, broker_port)
    logging.info(mySleepStateEval.client.start())

    # Subscribe to config change alert topic
    # TODO: for room in rooms:     mySleepStateEval.client.mySubscribe(main_topic + room + '/config_updates')
    logging.info(mySleepStateEval.client.mySubscribe(main_topic + 'config_updates'))

    try:
        while True:
            if mySleepStateEval.alarm_time:
                # Subscribe to motion sensor topic during the night
                if mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time:
                    logging.info(mySleepStateEval.client.mySubscribe(main_topic + 'bed'))

                    while mySleepStateEval.night_start <= datetime.now() <= mySleepStateEval.alarm_time:
                        time.sleep(5)
                        mySleepStateEval.evalState()

                    logging.info(mySleepStateEval.client.myUnsubscribe(main_topic + 'bed'))

    except KeyboardInterrupt:
        logging.info(mySleepStateEval.client.stop())
