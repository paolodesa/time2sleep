from MyMQTT import *
import json
import time
import requests


class LightControllerService:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.light = False

    def notify(self, topic, payload):
        if topic == main_topic + 'light':
            message = json.loads(payload)
            self.sensor_motion = message['data'][0]['value']

        if topic == main_topic + 'config_changed':
            message = json.load(payload)
            self.config_changed = true

    def LightOn(self):
        msg = json.dumps({'light': True})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = True

    def LightOff(self):
        msg = json.dumps({'light': False})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = False


if __name__ == '__main__':

    # -- Retrieve here the list of services from the catalogue
    # TODO
    rb_url = 'http://127.0.0.1:8080'
    main_topic = 'Time2sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = 1883

    # -- Retrieve here the config file from the RaspBerry
    r = requests.get(rb_url)
    config = r.json()
    print(config['alarm_time'])


    # -- Start subscription and publish actuators commands
    # TODO: make it scalable for many rooms

    # myLightController = LightControllerService('LightControllerService', broker_host, broker_port)
    # myLightController.client.start()
    # time.sleep(1)
    # myLightController.client.mySubscribe(main_topic + 'light')
    # try:
    #     while True:
    #         while not myLightController.light:
    #             if myLightController.sensor_motion >= 50:
    #                 myLightController.LightOn()
    #         while myLightController.light:
    #             if myLightController.sensor_motion < 50:
    #                 myLightController.LightOff()
    # except KeyboardInterrupt:
    #     myLightController.client.stop()
