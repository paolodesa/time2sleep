# Alarm scheduler microservice
include MyMQTT
include time
include json

class AlarmScheduler():
    def __init__(clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.state = ""
        self.alarm = 0

    def notify(topic, payload):
        data = json.load(payload)
            if topic == main_topic + 'bed/motion_sensor':
                self.sensor_motion = data['value']
            
            if topic == main_topic + '/state':
                self.state = data['state']
    
    def alarmStart():
        msg = json.dumps({'start_alarm'=1})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.alarm = 1
    
    def alarmStop():
        msg = json.dumps({'start_alarm'=0})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.alarm = 0
        
if __name__=='__name__':
    
    # I expect all the config information to be global and always updated. They are: wake_time.
    # Should I also check the vibration sensor?
    myAlarmScheduler = AlarmScheduler(clientID = 'AlarmSchedulerService', broker_host, broker_port)
    myAlarmScheduler.client.start()
    myAlarmScheduler.client.mySubscribe(main_topic + '/bed/motion_sensor')
    myAlarmScheduler.client.mySubscribe(main_topic + '/state')
    while myAlarmScheduler.alarm == 0:
        if (actualTime >= wake_time-10min and myAlarmScheduler.state == 'light') or actualTime > wake_time + 20min:
            myAlarmScheduler.alarmStart()
    while myAlarmScheduler.alarm == 1:
        if myAlarmScheduler.sensor_motion == 1:
            myAlarmScheduler.alarmStop()