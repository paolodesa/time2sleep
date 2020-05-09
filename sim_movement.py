import random
import time

if __name__ == '__main__':
    try:
        while True:
            print(random.randrange(0, 100))     # motion sensor output (set triggering threshold)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nGoodbye!')
