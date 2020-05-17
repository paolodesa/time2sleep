# Alarm scheduler microservice
include MyMQTT
include time
include json

class LightControllerService():
    def __init__(clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.light = False

    def notify(topic, payload):
        data = json.load(payload)
            if topic == main_topic + 'bed/motion_sensor':
                self.sensor_motion = data['value']
    
    def LightOn():
        msg = json.dumps({'light'=True})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.light = True
    
    def LightOff():
        msg = json.dumps({'light' = False})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.light = False
        
if __name__=='__name__':
    
    # I expect all the config information to be global and always updated. They are: wake_time.
    # Should I also check the vibration sensor?
    myLightController = LightControllerService(clientID = 'LightControllerService', broker_host, broker_port)
    myLightController.client.start()
    myLightController.client.mySubscribe(main_topic + '/bed/motion_sensor')
    while(True)
        while (myLightController.light == False):
            if (myLightController.sensor_motion == True):
                myLightController.LightOn()
        while (myLightController.light == True):
            if myLightController.sensor_motion == False:
                myLightController.LightOff()