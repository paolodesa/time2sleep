import random
import time

if __name__ == '__main__':
    try:
        while True:
            print(random.randrange(15, 30))     # temperature sensor output [°C]
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nGoodbye!')
