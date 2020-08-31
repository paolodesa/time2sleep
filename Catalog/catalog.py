import cherrypy
import json
import time
import datetime


class ServiceCatalog(object):
    exposed = True

    def __init__(self):
        pass

    def GET(self, *uri, **params):
        output = 'Time2Sleep Service Catalog'
        with open('t2s_catalog.json', 'r') as f:
            t2s_catalog = json.load(f)
            f.close()
        output += '<br><br>Current devices:'
        for x in t2s_catalog['devices']:
            output += '<br>' + str(x)
        output += '<br><br>Last updated: ' + datetime.datetime.fromtimestamp(t2s_catalog['last_updated']).strftime("%d/%m/%Y, %H:%M:%S")
        return output

    def POST(self, *uri, **params):
        if len(uri) == 1 and uri[0] == 'addDevice':
            try:
                with open('t2s_catalog.json', 'r+') as f:
                    t2s_catalog = json.load(f)
                    new_device_info = json.loads(cherrypy.request.body.read())
                    try:
                        ip = new_device_info['ip']
                        port = new_device_info['port']
                        services = new_device_info['services']
                    except KeyError:
                        f.close()
                        raise cherrypy.HTTPError(400, 'Bad request')

                    new_dev = {'ip': ip, 'port': port, 'services': services}

                    for d in t2s_catalog['devices']:
                        if (d['ip'] == ip):
                            t2s_catalog['devices'].pop(t2s_catalog['devices'].index(d))

                    t2s_catalog['devices'].append(new_dev)
                    t2s_catalog['last_updated'] = time.time()
                    f.seek(0)
                    f.write(json.dumps(t2s_catalog, indent=4, sort_keys=True))
                    f.truncate()
                    f.close()
                    return 'Catalog file successfully written'
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
                        if (d['ip'] == ip):
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
                    return 'Catalog file successfully written'
            except KeyError:
                raise cherrypy.HTTPError(404, 'The catalog file was not found')


if __name__ == '__main__':
    conf = {
        '/':
            {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
    }
    cherrypy.quickstart(ServiceCatalog(), '/', conf)
