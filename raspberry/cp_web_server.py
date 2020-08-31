import cherrypy
import json


class SimpleService(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open('../etc/t2s_conf.json', 'r') as f:
            t2s_conf = json.load(f)
            f.close()
        return json.dumps(t2s_conf)

    def POST(self, *uri, **params):
        # TODO: publish configuration changing time
        if len(uri) == 1 and uri[0] == 'changeConfig':
            try:
                with open('../etc/t2s_conf.json', 'r+') as f:
                    t2s_conf = json.load(f)
                    try:
                        alarm_time = params['alarmTime']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(404, 'One of the keys is missing')
                    t2s_conf['alarm_time'] = alarm_time
                    f.seek(0)
                    f.write(json.dumps(t2s_conf, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'Configuration file successfully written'
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
