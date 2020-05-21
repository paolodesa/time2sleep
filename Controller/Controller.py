from MyMQTT import *
import json
import time
import os


class Controller():
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.nightStart = 0
        self.wakeTime = 0

    def notify(self, topic, payload):
        data = json.load(payload)
        if topic == main_topic + 'sleepTime':
            self.nightStart = data['nightStartTime']
            self.wakeTime = data['wakeUpTime']


if __name__ == '__main__':
    # we will retrieve a brokerhost and brokerport from the catalog

    myController = Controller('Controller', broker_host, broker_port)
    myController.client.start()
    myController.client.mySubscribe(main_topic + '/sleepTime')
    service = True
    service2 = True
    while True:
        if time >= nightStart:
            if service:
                service = False
                os.system('python LightControllerService.py')
                os.system('python SleepStateService.py')
        if time >= wakeTime:
            if service2:
                service2 = False
                os.kill('python LightControllerService.py')
                os.kill('python SleepStateService.py')
                os.system('python AlarmSchedulerService.py')
