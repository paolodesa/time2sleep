import sys
sys.path.insert(0, "../")
import cherrypy
import json
import requests
import time
import socket
from etc.MyMQTT import *


class ConfigUpdatePublisher:
    def __init__(self, clientID, broker_host, broker_port):
        self.client = MyMQTT(clientID, broker_host, broker_port, self)


class SimpleService(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open('../etc/t2s_conf.json', 'r') as f:
            t2s_conf = json.load(f)
            f.close()
        return json.dumps(t2s_conf)

    def POST(self, *uri):
        # TODO: publish configuration changing time
        if len(uri) == 1 and uri[0] == 'changeConfig':
            try:
                with open('../etc/t2s_conf.json', 'r+') as f:
                    t2s_conf = json.load(f)
                    config_update = json.loads(cherrypy.request.body.read())
                    try:
                        night_start = config_update['night_start']
                        alarm_time = config_update['alarm_time']
                        alarm_set = config_update['alarm_set']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'One of the keys is missing')
                    t2s_conf['night_start'] = night_start
                    t2s_conf['alarm_time'] = alarm_time
                    t2s_conf['alarm_set'] = alarm_set
                    f.seek(0)
                    f.write(json.dumps(t2s_conf, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    catalogue = requests.get('http://127.0.0.1:8082').json()
                    broker_host = catalogue['broker_host']
                    broker_port = catalogue['broker_port']
                    myConfigUpdatePublisher = ConfigUpdatePublisher('ConfigUpdatePublisher', broker_host, broker_port)
                    myConfigUpdatePublisher.client.start()
                    myConfigUpdatePublisher.client.myPublish(f'{t2s_conf["network_name"]}/{t2s_conf["room_name"]}/config_updates', json.dumps(t2s_conf))
                    myConfigUpdatePublisher.client.stop()
                    return 'Configuration file successfully written and published to broker'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The configuration file was not found')
        elif len(uri) == 1 and uri[0] == 'toggleLight':
            try:
                with open('../etc/t2s_conf.json', 'r+') as f:
                    t2s_conf = json.load(f)
                    config_update = json.loads(cherrypy.request.body.read())
                    try:
                        light_set = config_update['light_set']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'One of the keys is missing')
                    t2s_conf['light_set'] = light_set
                    f.seek(0)
                    f.write(json.dumps(t2s_conf, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    catalogue = requests.get('http://127.0.0.1:8082').json()
                    broker_host = catalogue['broker_host']
                    broker_port = catalogue['broker_port']
                    myConfigUpdatePublisher = ConfigUpdatePublisher('ConfigUpdatePublisher', broker_host, broker_port)
                    myConfigUpdatePublisher.client.start()
                    myConfigUpdatePublisher.client.myPublish(f'{t2s_conf["network_name"]}/{t2s_conf["room_name"]}/config_updates', json.dumps(t2s_conf))
                    myConfigUpdatePublisher.client.stop()
                    return 'Configuration file successfully written and published to broker'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The configuration file was not found')

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    def pingCatalog(self):
        catalog_host = '127.0.0.1'
        catalog_port = 8082
        url = f'http://{catalog_host}:{catalog_port}/addDevice'
        ip = self.get_ip_address()
        port = 8080
        with open('../etc/t2s_conf.json', 'r') as f:
            conf = json.load(f)
            f.close()
        name = conf['room_name']
        sensors = ['vibration', 'motion', 'noise', 'temperature', 'humidity']
        actuators = ['light', 'alarm']
        body = {'ip': ip, 'port': port, 'name': name, 'sensors': sensors, 'actuators': actuators, 'last_seen': time.time()}
        requests.post(url, json.dumps(body))


if __name__ == '__main__':
    s = SimpleService()
    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.tree.mount(s,'/',conf)
    cherrypy.engine.start()
    
    while True:
        try:
            s.pingCatalog()
            time.sleep(10)
        except KeyboardInterrupt:
            cherrypy.engine.exit()

