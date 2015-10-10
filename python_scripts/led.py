import RPi.GPIO as GPIO
import time, sys

GPIO.setmode(GPIO.BCM)

GPIO.setwarnings(False)
GPIO.setup(23,GPIO.OUT)

start_time = time.time()

print sys.argv[1]
loops = sys.argv[1]
counter = 0

print "starting," + str(counter) + str(loops)

# seriously, what the fuck am I doing wrong here
while counter != loops:
	print counter, loops
	print counter != loops
		
	GPIO.output(23,GPIO.HIGH)

	time.sleep(1)
	GPIO.output(23,GPIO.LOW)
	time.sleep(1)
	counter += 1

GPIO.output(23, GPIO.LOW)
