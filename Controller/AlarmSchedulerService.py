from MyMQTT import *
import json
import datetime as dt

class AlarmScheduler:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.state = ""
        self.alarm = 0

    def notify(self, topic, payload):
        data = json.load(payload)
        if topic == main_topic + 'bed/motion_sensor':
            self.sensor_motion = data['value']

        if topic == main_topic + '/sleep_state':
            self.state = data['sleep_state']

    def alarmStart(self):
        msg = json.dumps({'start_alarm':1})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.alarm = 1
    
    def alarmStop(self):
        msg = json.dumps({'start_alarm':0})
        self.client.myPublish(main_topic + '/actuators', msg)
        self.alarm = 0


if __name__=='__main__':
    
    # I expect all the config information to be global and always updated. They are: wake_time.
    # Should I also check the vibration sensor?
    main_topic = 'Time2sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = 1883
    wake_time = dt.datetime.now().replace(hour=7, minute=30)
    myAlarmScheduler = AlarmScheduler('AlarmSchedulerService', broker_host, broker_port)
    myAlarmScheduler.client.start()
    myAlarmScheduler.client.mySubscribe(main_topic + 'bed')
    myAlarmScheduler.client.mySubscribe(main_topic + 'state')

    while myAlarmScheduler.alarm == 0:
        if (dt.datetime.now() >= wake_time-dt.timedelta(minutes=10) and myAlarmScheduler.state == 'light') or dt.datetime.now() > wake_time + dt.timedelta(minutes=20):
            myAlarmScheduler.alarmStart()
    while myAlarmScheduler.alarm == 1:
        if myAlarmScheduler.sensor_motion == 1:
            myAlarmScheduler.alarmStop()