import random
import json
import time
from simplePublisher import *


class Sensor(MyPublisher):

    def __init__(self, clientID, topic_type, sensor_type):
        self.clientID = str(clientID)
        self.topic_type = topic_type
        self.sensor_type = sensor_type
        self.topic = '/'.join([self.topic_type, self.sensor_type])
        MyPublisher.__init__(self, self.clientID)
        self.message = {'type': self.sensor_type, 'value': '', 'unit': '%', 'timestamp': ''}

    def myPublish(self, topic, message):
        self._paho_mqtt.publish(topic, message, 2)

    def sendData(self):
        self.message['value'] = random.randint(0, 100)
        self.message['timestamp'] = str(time.time())
        self.myPublish(self.topic, json.dumps(self.message))


if __name__ == '__main__':
    topic_type = 'weather'
    sensor_type = 'humidity'
    s_ID = 0
    sensor = Sensor(s_ID, topic_type, sensor_type)
    sensor.start()

    try:
        while True:
            sensor.sendData()
            time.sleep(1)
    except KeyboardInterrupt:
        sensor.stop()
        print("\nGoodbye!")
