import random
import json
import time
from simplePublisher import *


class Sensor(MyPublisher):
    """Topics are published with the following structure Time2Sleep/bedroomN/sensor_area (N=1,2,3 & sensor_area=weather,bed,light)"""

    def __init__(self, project, room, sensor, broker):
        self.project = project
        self.room = room
        self.sensor = str(sensor)
        self.topic = '/'.join([self.project, self.room, self.sensor])
        MyPublisher.__init__(self, self.sensor)
        if sensor == 'weather':
            self.message = {
                'project': self.project,
                'room': self.room,
                'sensor_area': self.sensor,
                'data':
                    [
                        {'type': 'temperature', 'value': '', 'timestamp': '', 'unit': 'C'},
                        {'type': 'humidity', 'value': '', 'timestamp': '', 'unit': '%'}
                    ]
            }
        elif sensor == 'bed':
            self.message = {
                'project': self.project,
                'room': self.room,
                'sensor_area': self.sensor,
                'data':
                    [
                        {'type': 'vibration', 'value': '', 'timestamp': '', 'unit': '%'},
                        {'type': 'noise', 'value': '', 'timestamp': '', 'unit': 'dB'},
                        {'type': 'motion', 'value': '', 'timestamp': '', 'unit': '%'}
                    ]
            }
        elif sensor == 'light':
            self.message = {
                'project': self.project,
                'room': self.room,
                'sensor_area': self.sensor,
                'data':
                    [
                        {'type': 'motion', 'value': '', 'timestamp': '', 'unit': '%'}
                    ]
            }

    def myPublish(self, topic, message):
        self._paho_mqtt.publish(topic, message, 2)

    def sendData(self):
        if self.sensor == 'weather':
            self.message['data'][0]['value'] = random.randint(10, 30)
            self.message['data'][1]['value'] = random.randint(50, 90)
            self.message['data'][0]['timestamp'] = str(time.time())
            self.message['data'][1]['timestamp'] = str(time.time())
        elif self.sensor == 'bed':
            self.message['data'][0]['value'] = random.randint(0, 100)
            self.message['data'][1]['value'] = random.randint(20, 90)
            self.message['data'][2]['value'] = random.randint(0, 100)
            self.message['data'][0]['timestamp'] = str(time.time())
            self.message['data'][1]['timestamp'] = str(time.time())
            self.message['data'][2]['timestamp'] = str(time.time())
        elif self.sensor == 'light':
            self.message['data'][0]['value'] = random.randint(0, 100)
            self.message['data'][0]['timestamp'] = str(time.time())

        self.myPublish(self.topic, json.dumps(self.message))


if __name__ == '__main__':
    Sensors = []
    project = 'Time2sleep'
    rooms = ['bedroom1', 'bedroom2',
             'bedroom3']  # puoi cambiare il numero del range in base al numero delle stanze che vuoi
    sensor_area = ['weather', 'bed', 'light']
    broker = '127.0.0.1'  # è il valore di default locale di tutti i pc
    n_sensors = 0
    for room in rooms:
        for s in sensor_area:
            sensor = Sensor(project, room, s, broker)
            Sensors.append(sensor)
            n_sensors = n_sensors + 1  # alla fine del ciclo n_sensors vale 9 (3 topic in ogni stanza)

    for sensor in Sensors:
        sensor.start()

    while True:
        try:
            for sensor in Sensors:
                sensor.sendData()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing the connection...")
            for sensor in Sensors:
                sensor.stop()
            break

    print("Goodbye")
