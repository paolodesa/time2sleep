include MyMQTT
include json

class LightControllerService():
    def __init__(clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.light = False

    def notify(topic, payload):
        if topic == main_topic + 'bed':
            message = json.load(payload)
            self.sensor_motion = message['data'][0]['value']
    
    def LightOn():
        msg = json.dumps({'light'=True})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.light = True
    
    def LightOff():
        msg = json.dumps({'light' = False})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.light = False
        
if __name__=='__main__':
    
    # I expect all the config information to be global and always updated. They are: wake_time.
    # Should I also check the vibration sensor?
    main_topic = 'Time2Sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = '1883'
    
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
