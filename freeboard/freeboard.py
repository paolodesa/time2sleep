import cherrypy
import os
import json


class Freeboard(object):
    exposed = True

    def __init__(self):
        self.id = 1

    def GET(self):
        return open('./index.html')

    def POST(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'saveDashboard':
            try:
                dash_conf = json.loads(params['json_string'])
            except TypeError:
                return 'The request body is not json formatted'
            except KeyError:
                return 'The config parameter was not found'
            with open('./dashboard/dashboard.json', 'r+') as json_conf:
                json_conf.seek(0)
                json_conf.write(json.dumps(dash_conf, indent=4, sort_keys=True))
                json_conf.truncate()
                json_conf.close()
            return 'Config file successfully written'


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
        },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './css'
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './js'
        },
        '/dashboard': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './dashboard'
        },
        '/img': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './img'
        },
        '/plugins': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './plugins'
        },
    }
    cherrypy.tree.mount(Freeboard(), '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8084})
    cherrypy.engine.start()
    cherrypy.engine.block()
