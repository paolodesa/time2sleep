from etc.MyMQTT import *
import json
from datetime import datetime
import requests
import logging

# The new idea is that of creating an instance of LightControllerService per room, and let it manage
# that room autonomously. Therefore all the logic is moved inside the notify method.

THRESHOLD = 50


class LightControllerService:
    def __init__(self, clientID, rb_url, broker_host, broker_port):

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.rb_url = rb_url
        self.night_start = 0
        self.alarm_time = 0

        self.sensor_motion = 0
        self.light_on = False
        self.last_update = ''

        self.updateConfig()

    def notify(self, topic, payload):
        if topic == main_topic + 'light':
            message = json.loads(payload)
            self.sensor_motion = message['data'][0]['value']

        # TODO: if topic == main_topic/*/ + 'config_updates': room = topic.parse('/')[1]
        if topic == main_topic + 'config_updates':
            self.updateConfig()
            self.last_update = message

    def LightOn(self):
        msg = json.dumps({'light': True})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light_on = True
        logging.debug(self.client.clientID + 'LIGHT ON')

    def LightOff(self):
        msg = json.dumps({'light': False})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light_on = False
        logging.debug(self.client.clientID + 'LIGHT OFF')

    def updateConfig(self):
        # -- Retrieve here the config file from the RaspBerry
        r = requests.get(self.rb_url)
        config_dict = r.json()
        self.night_start = datetime.strptime(config_dict['night_start'], '%y,%m,%d,%H,%M')
        self.alarm_time = datetime.strptime(config_dict['alarm_time'], '%y,%m,%d,%H,%M')
        logging.info(self.client.clientID + ' CONFIG - night_start: %s, alarm_time: %s', self.night_start, self.alarm_time)


if __name__ == '__main__':

    logging.basicConfig(filename='../logs/light_controller_service.log', filemode='w', level=logging.DEBUG,
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

    # Instantiate and start the light controller
    logging.info('Instantiating the controller')
    myLightController = LightControllerService('LightControllerService', rb_url, broker_host, broker_port)
    logging.info(myLightController.client.start())

    # Subscribe to config change alert topic
    # TODO: for room in rooms:     myLightController.client.mySubscribe(main_topic + room + '/config_updates')
    logging.info(myLightController.client.mySubscribe(main_topic + 'config_updates'))

    try:
        while True:
            # Subscribe to motion sensor topic during the night
            if myLightController.night_start <= datetime.now() <= myLightController.alarm_time:
                logging.info(myLightController.client.mySubscribe(main_topic + 'light'))

                while myLightController.night_start <= datetime.now() <= myLightController.alarm_time:
                    if not myLightController.light_on:
                        if myLightController.sensor_motion >= THRESHOLD:
                            myLightController.LightOn()
                    else:
                        if myLightController.sensor_motion < THRESHOLD:
                            myLightController.LightOff()

                logging.info(myLightController.client.myUnsubscribe(main_topic + 'light'))

    except KeyboardInterrupt:
        logging.info(myLightController.client.stop())
