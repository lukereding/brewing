#!/usr/bin/python
import sys, time, logging
from apscheduler.scheduler import Scheduler
import smtplib
from email.mime.text import MIMEText
# use pip install apscheduler==2.1.2
# see here: https://pythonadventures.wordpress.com/2013/08/06/apscheduler-examples/
import os, glob, csv
from twilio.rest import TwilioRestClient
import RPi.GPIO as io

# basic idea:
## recordAndRegulateTemp is the main function. Takes arguments number_of_hours, a message to print to stdout, and a temperature
## it runs every minute (although that can be changed)
## when a given temperature is done, you can call the function again with a different temperature

# to do: arguments for name to brew log, temps, time
## to do:: keep a list of tuples with (datem temp) for plotting

def send_email(message):
	fromaddr = 'lukereding@gmail.com'
	toaddrs  = 'lukereding@gmail.com'
	msg = MIMEText(message)
	msg['Subject'] = 'a message from your fermenter'
	username = 'lukereding'	
	password = 'Marlinspike1200'
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,password)
	server.sendmail(fromaddr, toaddrs, msg.as_string())
	server.quit()

def my_job(temp,csvWriter):
	
	try:
		# try grabbing to current temp and writing it to the csv file
		current_temp = read_temp()
		print current_temp
		csvWriter.writerow((current_temp, time.strftime("%d/%m/%Y"),time.strftime("%H:%M:%S")) )
	except: # send an email if you can't
		send_email("can't read the temperature")
	
	# now to regulate the temperature:
	if current_temp > (temp + 1.5):
		print "turning on the fridge"
		## turn on the power source
		io.output(power_pin, True)
		logging.info("temperature is " + str(current_temp))
		logging.info("turned on the mini fridge")
	elif current_temp < (temp - 1.5):
		print "turning off the fridge"
		## turn off mini fridge
		io.output(power_pin, False)
		logging.info("temperature is " + str(current_temp))
		logging.info("turned off mini fridge")
	else:
		print "temp in the fridge looks good"
		# turn off mini fridge if it's on:
		io.output(power_pin, False)
		logging.info("temperature is " + str(current_temp))
		logging.info("no need to turn on mini fridge")

def recordAndRegulateTemp(number_of_hours,temperature,csvWriter):
	sched = Scheduler()
	sched.start()
	job = sched.add_interval_job(my_job, minutes=5, args = [temperature,csvWriter])
	
	start_time = time.time()
	while time.time() - start_time < (3600*number_of_hours):
		text = "time left: " + str(round((3600*number_of_hours) - (time.time()-start_time),0))+ " seconds\n"
		sys.stdout.write(text); sys.stdout.flush()		
		time.sleep(60)
	
	sched.unschedule_job(job)

# read the raw temperatures
def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

# process raw temps
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
		return temp_f

def send_text(message):
	client.messages.create(to='+12406788175',from_='+12406502503',body = message)




if __name__ == "__main__":
	
	# set up for text messaging
	client = TwilioRestClient(account='AC9f4bde03d72a5f180728775df6ff9f6f', token='1daf47463af52561cb25ecff78694493')
	
	# set up the temperature probe
	try:
		os.system('modprobe w1-gpio')
		os.system('modprobe w1-therm')
		base_dir = '/sys/bus/w1/devices/'
		device_folder = glob.glob(base_dir + '28*')[0]
		device_file = device_folder + '/w1_slave'
	except:
		send_text("could not find the thermometer. program is exiting")
		send_email("seems like there's something wrong with how the program is attempting to interact with the temperature probe. the program is exiting")
		sys.exit()
	
	# set up gpio pins to regulate fridge
	io.setmode(io.BCM)
	power_pin = 23 # might be different for you
	try:
		io.setup(power_pin,io.OUT)
		io.output(power_pin, False)
	except:
		send_email("check to make sure the relay is hooked up correctly")
	
	# set up csv writing
	file = open("tempRecordings.csv", 'wb')
	writer = csv.writer(file)

	# set up logging
	logging.basicConfig(filename="/home/pi/Desktop/logs/brew.log",level=logging.DEBUG,format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
	
	sched = Scheduler()
	sched.start()
	
	# this is the heart of the program:
	# send email to let me know I'm brewing
	send_email("starting brew log. target temperature is 78 for now")
	# main functions:
	recordAndRegulateTemp(36,78,writer)
	send_email("changing temperature to 75")
	recordAndRegulateTemp(12,75,writer)
	send_email("changing temperature to 72")
	recordAndRegulateTemp(72,72,writer)
	send_email("changing temperature to 75")
	recordAndRegulateTemp(24,75,writer)
	send_email("changing temperature to 80")
	recordAndRegulateTemp(20,80,writer)
	print "program done. fermenter shutting down."
	send_email("ending. fermenter is shutting off")
	io.output(power_pin, False)
