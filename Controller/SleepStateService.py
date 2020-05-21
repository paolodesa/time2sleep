from MyMQTT import *
import json
import time


class SleepStateEval:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.sensor_motion = 0
        self.sensor_noise = 0
        self.sensor_vibration = 0
        self.state = "light"

    def notify(self, topic, payload):
        data = json.load(payload)
        if topic == main_topic + 'bed/motion_sensor':
            self.sensor_motion = data['value']

        if topic == main_topic + 'bed/noise_sensor':
            self.sensor_noise = data['value']

        if topic == main_topic + 'bed/vibration_sensor':
            self.sensor_vibration = data['value']

        msg = json.dumps({'sleep_state': self.state})
        self.client.myPublish(main_topic + '/sleep_state', msg)


if __name__ == '__main__':
    THRESHOLD = 100

    # I expect all the config information to be global and always updated.
    # They are: broker_host, broker_port, main_topic, night_start, night_end.
    main_topic = 'Time2sleep/bedroom1/'
    broker_host = '127.0.0.1'
    broker_port = 1883

    mySleepStateEval = SleepStateEval('SleepStateService', broker_host, broker_port)
    mySleepStateEval.client.start()
    mySleepStateEval.client.mySubscribe(main_topic + 'bed')
    while True:
        if mySleepStateEval.sensor_motion + mySleepStateEval.sensor_noise + mySleepStateEval.sensor_vibration > THRESHOLD:
            mySleepStateEval.state = 'light'
        else:
            mySleepStateEval.state = 'deep'
