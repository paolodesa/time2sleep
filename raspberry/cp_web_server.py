import sys
sys.path.insert(0, "../")
import cherrypy
import json
import requests
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


if __name__ == '__main__':
    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.quickstart(SimpleService(), '/', conf)
