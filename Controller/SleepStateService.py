# Sleepstate evaluate microservice
include MyMQTT
include time
include json

class SleepStateEval():
    def __init__(clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.sensor_noise = 0
        self.sensor_vibration = 0
        self.state = "light"

    def notify(topic, payload):
    data = json.load(payload)
        if topic == main_topic + 'bed/motion_sensor':
            self.sensor_motion = data['value']
        
        if topic == main_topic + 'bed/noise_sensor':
            self.sensor_noise = data['value']
            
        if topic == main_topic + 'bed/vibration_sensor':
            self.sensor_vibration = data['value']
        msg = json.dumps({'state'=self.state})    
        self.client.myPublish(main_topic + '/state', msg)
        
if __name__=='__name__':
    THRESHOLD = 10
    
    # I expect all the config information to be global and always updated. They are: broker_host, broker_port, main_topic, night_start, night_end.
    mySleepStateEval = SleepStateEval(clientID = 'SleepStateService', broker_host, broker_port)
    mySleepStateEval.client.start()
    mySleepStateEval.client.mySubscribe(main_topic + '/bed/+')
    while True:
        if mySleepStateEval.sensor_motion + mySleepStateEval.sensor_noise + mySleepStateEval.sensor_vibration > THRESHOLD
            mySleepStateEval.state = 'light'
        else:
            mySleepStateEval.state = 'deep'