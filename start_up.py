import sys
sys.path.insert(0, "./raspberry")
sys.path.insert(0, "./etc")
exec(open("raspberry/cp_web_server.py").read())

# os.system('python3 ~/time2sleep/raspberry/cp_web_server.py')
# os.system('python3 ~/time2sleep/raspberry/sensors_reader.py')
# os.system('python3 ~/time2sleep/raspberry/AlarmActuatorService.py')
# os.system('python3 ~/time2sleep/raspberry/LightActuatorService.py')
