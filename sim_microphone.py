import random
import time

if __name__ == '__main__':
    try:
        while True:
            print(random.randrange(10, 100))     # microphone input loudness [dB]
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nGoodbye!')
