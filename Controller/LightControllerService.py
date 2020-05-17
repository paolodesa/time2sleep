from MyMQTT import *
import json
import time

class LightControllerService():
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.light = False

    def notify(self, topic, payload):
        if topic == main_topic + 'light':
            message = json.loads(payload)
            self.sensor_motion = message['data'][0]['value']
    
    def LightOn(self):
        msg = json.dumps({'light':True})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = True
    
    def LightOff(self):
        msg = json.dumps({'light':False})
        self.client.myPublish(main_topic + 'actuators', msg)
        self.light = False
        
if __name__=='__main__':
    
    # I expect all the config information to be global and always updated. They are: wake_time.
    # Should I also check the vibration sensor?
    main_topic = 'Time2sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = 1883
    
    myLightController = LightControllerService('LightControllerService', broker_host, broker_port)
    myLightController.client.start()
    time.sleep(1)
    myLightController.client.mySubscribe(main_topic + 'light')
    try:
        while(True):
            while (myLightController.light == False):
                if (myLightController.sensor_motion >= 50):
                    myLightController.LightOn()
            while (myLightController.light == True):
                if myLightController.sensor_motion < 50:
                    myLightController.LightOff()
    except KeyboardInterrupt:
        myLightController.client.stop()
