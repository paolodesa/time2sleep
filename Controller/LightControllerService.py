from MyMQTT import *
import json
import time
import requests


class LightControllerService:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.config_changed = ''
        self.light = False

    def notify(self, topic, payload):
        if topic == main_topic + 'light':
            message = json.loads(payload)
            self.sensor_motion = message['data'][0]['value']

        if topic == main_topic + 'config_changed':
            message = json.load(payload)
            self.config_changed = True

    def LightOn(self):
        msg = json.dumps({'light': True})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = True

    def LightOff(self):
        msg = json.dumps({'light': False})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = False


if __name__ == '__main__':

    # -- Retrieve here the list of services and devices from the cataloguest
    # TODO
    rb_url = 'http://127.0.0.1:8080'
    main_topic = 'Time2sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = 1883

    # -- Retrieve here the config file from the RaspBerry
    # TODO: make it scalable for many rooms
    r = requests.get(rb_url)
    config_dict = r.json()
    night_start = config_dict['night_start']
    alarm_time = config_dict['alarm_time']


    # -- Start subscription and publish actuators commands
    # TODO: make it scalable for many rooms

    myLightController = LightControllerService('LightControllerService', broker_host, broker_port)
    while True:
        myLightController.client.start()
        myLightController.client.mySubscribe('TOPIC TO WARN ABOUT CONFIG CHANGES')
        if myLightController.config_changed: # <----- SISTEMARE QUA
            config_dict = requests.get(rb_url).json()
            night_start = config_dict['night_start']
            alarm_time = config_dict['alarm_time']
            myLightController.config_changed = False

        while night_start <= time.time() <= alarm_time:
            time.sleep(1)
            myLightController.client.mySubscribe(main_topic + 'light')
            try:
                while True:
                    while not myLightController.light:
                        if myLightController.sensor_motion >= 50:
                            myLightController.LightOn()
                    while myLightController.light:
                        if myLightController.sensor_motion < 50:
                            myLightController.LightOff()
            except KeyboardInterrupt:
                myLightController.client.stop()

        myLightController.client.stop()
