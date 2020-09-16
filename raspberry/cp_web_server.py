from datetime import datetime, timedelta
import sys

sys.path.insert(0, "../")
import cherrypy
import json
import requests
import time
import socket
from etc.MyMQTT import *
from etc.globalVar import CATALOG_ADDRESS


class ConfigManager:
    def __init__(self, clientID, broker_host, broker_port):
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.client = MyMQTT(clientID, broker_host, broker_port, self)
        self.t2s_config = None
        self.main_topic = ''
        self.update_config()

    def update_config(self):
        try:
            with open('../etc/t2s_conf.json', 'r') as f:
                self.t2s_config = json.load(f)
                self.main_topic = self.t2s_config['network_name'] + '/' + self.t2s_config['room_name']
                if not self.client.isSubscriber:
                    self.client.mySubscribe(self.main_topic + '/sleep_state')
        except OSError:
            return 'Configuration file not found'

    def notify(self, topic, payload):
        message = json.loads(payload)
        if topic == self.main_topic + '/sleep_state':
            if message['sleep_state'] == 'awake':
                new_night_start = datetime.strftime(self.t2s_config['night_start'] + timedelta(days=1), '%Y,%m,%d,%H,%M')
                new_alarm_time = datetime.strftime(self.t2s_config['alarm_time'] + timedelta(days=1), '%Y,%m,%d,%H,%M')
                self.t2s_config['nigh_start'] = new_night_start
                self.t2s_config['alarm_time'] = new_alarm_time

                self.save_config(self.t2s_config)

    def save_config(self, new_config):
        with open('../etc/t2s_conf.json', 'w') as f:
            f.write(json.dumps(new_config, indent=4, sort_keys=True))
        self.update_config()

    def publish_update(self):
        with open('../etc/t2s_conf.json', 'r') as f:
            t2s_conf = json.load(f)

            # Publish on the broker that a new configuration is available for this room
            msg = json.dumps({"timestamp": str(time.time())})
            self.client.myPublish(self.main_topic + '/config_updates', msg)


class SimpleService(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        try:
            with open('../etc/t2s_conf.json', 'r') as f:
                t2s_conf = json.load(f)
                f.close()
            return json.dumps(t2s_conf)
        except OSError:
            return None

    def POST(self, *uri):
        if len(uri) == 1 and uri[0] == 'changeConfig':
            config_update = json.loads(cherrypy.request.body.read())
            myConfigManager.save_config(config_update)
            myConfigManager.publish_update()
            return 'Configuration file successfully written and published to broker'

        # elif len(uri) == 1 and uri[0] == 'toggleLight':
        #     # function to manually toggle the light on
        #     try:
        #         with open('../etc/t2s_conf.json', 'r+') as f:
        #             t2s_conf = json.load(f)
        #             config_update = json.loads(cherrypy.request.body.read())
        #             try:
        #                 light_set = config_update['light_set']
        #             except KeyError:
        #                 f.close()
        #                 raise cherrypy.HTTPError(400, 'One of the keys is missing')
        #             t2s_conf['light_set'] = light_set
        #             f.seek(0)
        #             f.write(json.dumps(t2s_conf, indent=4, sort_keys=True))
        #             f.truncate()
        #             f.close()
        #             myConfigManger.client.myPublish(
        #                 f'{t2s_conf["network_name"]}/{t2s_conf["room_name"]}/config_updates', json.dumps(t2s_conf))
        #             myConfigManager.client.stop()
        #             return 'Configuration file successfully written and published to broker'
        #     except KeyError:
        #         raise cherrypy.HTTPError(404, 'The configuration file was not found')

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    def pingCatalog(self):
        ip = self.get_ip_address()
        port = 8080
        with open('../etc/t2s_conf.json', 'r') as f:
            conf = json.load(f)
            f.close()
        name = conf['room_name']
        sensors = conf['sensors']
        actuators = conf['actuators']
        body = {'ip': ip, 'port': port, 'name': name, 'sensors': sensors, 'actuators': actuators,
                'last_seen': time.time()}
        print(body)
        requests.post(CATALOG_ADDRESS + '/addDevice', json.dumps(body))


if __name__ == '__main__':
    catalogue = requests.get(CATALOG_ADDRESS).json()
    broker_host = catalogue['broker_host']
    broker_port = catalogue['broker_port']
    myConfigManager = ConfigManager('ConfigManager_', broker_host, broker_port)

    s = SimpleService()
    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.tree.mount(s, '/', conf)
    cherrypy.engine.start()

    while True:
        try:
            s.pingCatalog()
            time.sleep(10)
        except KeyboardInterrupt:
            cherrypy.engine.exit()
            break
