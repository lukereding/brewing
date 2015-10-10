#!/usr/bin/python
import os, glob, csv, time, sys
from twilio.rest import TwilioRestClient

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

file = open("tempRecordings.csv", 'wb')
writer = csv.writer(file)
counter = 0

# for sending text messages
client = TwilioRestClient(account='AC9f4bde03d72a5f180728775df6ff9f6f', token='1daf47463af52561cb25ecff78694493')

max_temp = 90

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		writer.writerow( (temp_c, temp_f, time.strftime("%d/%m/%Y"),time.strftime("%H:%M:%S")) )
		return temp_c, temp_f

while True:
	print read_temp(), time.strftime("%d/%m/%Y"), time.strftime("%H:%M%S")
	cel, far = read_temp()
	if far > max_temp and counter % 6 == 0:
		client.messages.create(to='+12406788175',from_='+12406502503',body = "your house is " + str(far) + " degrees F")
	print "read temperature. sleeping for 10 minutues"
	time.sleep(600)
	counter += 1

print "exited"
