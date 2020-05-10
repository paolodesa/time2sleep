import cherrypy
import json


class SimpleService(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        output = 'Time2Sleep Web Service'
        '''if len(uri) != 0:
            output += '<br>uri: ' + ','.join(uri)
        if params != {}:
            output += '<br>params: ' + str(params)'''
        with open('t2s_conf.json', 'r') as f:
            t2s_conf = json.load(f)
            f.close()
        for x in t2s_conf:
            output += '<br><br>Current config:<br><br>' + x + ': ' + str(t2s_conf[x])
        return output

    def POST(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'changeConfig':
            try:
                with open('t2s_conf.json', 'r+') as f:
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
