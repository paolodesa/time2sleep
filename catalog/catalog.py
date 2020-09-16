import cherrypy
import json
import time
import datetime


class ServiceCatalog(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        with open('t2s_catalog.json', 'r') as f:
            t2s_catalog = json.load(f)
            f.close()
        return json.dumps(t2s_catalog)

    def POST(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'addDevice':
            try:
                with open('t2s_catalog.json', 'r+') as f:
                    t2s_catalog = json.load(f)
                    new_device_info = json.loads(cherrypy.request.body.read())
                    try:
                        ip = new_device_info['ip']
                        port = new_device_info['port']
                        name = new_device_info['name']
                        sensors = new_device_info['sensors']
                        actuators = new_device_info['actuators']
                        last_seen = new_device_info['last_seen']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_dev = {'ip': ip, 'port': port, 'name': name, 'sensors': sensors, 'actuators': actuators, 'last_seen': last_seen}

                    for d in t2s_catalog['devices']:
                        if d['ip'] == ip:
                            t2s_catalog['devices'].pop(t2s_catalog['devices'].index(d))

                    t2s_catalog['devices'].append(new_dev)
                    t2s_catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(t2s_catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')
        if len(uri) == 1 and uri[0] == 'removeDevice':
            try:
                with open('t2s_catalog.json', 'r+') as f:
                    t2s_catalog = json.load(f)
                    new_device_info = json.loads(cherrypy.request.body.read())
                    try:
                        ip = new_device_info['ip']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    found = False
                    for d in t2s_catalog['devices']:
                        if d['ip'] == ip:
                            t2s_catalog['devices'].pop(t2s_catalog['devices'].index(d))
                            found = True

                    if found is False:
                        f.close()
                        raise cherrypy.HTTPError(404, "Device not found")

                    t2s_catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(t2s_catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')

    def removeInactive(self):
        removingDev = False
        with open('t2s_catalog.json', 'r+') as f:
            t2s_catalog = json.load(f)
            for d in t2s_catalog['devices']:
                if time.time() - d['last_seen'] > 10:
                    t2s_catalog['devices'].pop(t2s_catalog['devices'].index(d))
                    t2s_catalog['last_updated'] = time.time()
                    removingDev = True
            if removingDev:
                f.seek(0)
                f.write(json.dumps(t2s_catalog, indent=4, sort_keys=True))
                f.truncate()
                f.close()
            else:
                f.close()


if __name__ == '__main__':
    catalog = ServiceCatalog()
    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8082})
    cherrypy.tree.mount(catalog, '/', conf)
    cherrypy.engine.start()

    while True:
        try:
            catalog.removeInactive()
            time.sleep(2)
        except KeyboardInterrupt:
            cherrypy.engine.exit()
            break
