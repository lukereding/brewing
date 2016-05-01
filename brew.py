#!/usr/bin/python
import sys, time, logging
from apscheduler.scheduler import Scheduler # for checking the temperature at regular intervals
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
# use pip install apscheduler==2.1.2
# see here: https://pythonadventures.wordpress.com/2013/08/06/apscheduler-examples/
import os, glob, csv
from twilio.rest import TwilioRestClient # for texting capabilities
import RPi.GPIO as io # for manipulating pins

# for plotting
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys   # for arguments

'''
basic idea:
recordAndRegulateTemp is the main function. The first argument you pass it should be the name of your brew, which should be unique. Then enter the temperature you want the fridge to hold, followed by the number of hours that the temperature should be held for. Repeat. See example below. 
The temperature is checked every five minutes (although that can be changed).
You get emails with a graph every 12 hours, and you get an email whenever the temperature is set to change.

example line to run brew pi
this will save all stdout to a .log file and allow you to run everything in the background
ssh-ing out of your pi will not affect the running of the script

sudo nohup python -u brew.py dubbelTrouble 80 24 78 12 75 12 72 12 70 60 75 24 80 24 >> brewPySTDOUTDubbelTrouble.log 2>&1 &

'''
# to do: arguments for name to brew log, temps, time
## to do:: keep a list of tuples with (datem temp) for plotting

def plot_temps(temps,annotation):
		
	# convert to np array to maintain compatibility with other function
	temps = np.asarray(temps)
	
	# determine sliding window size based on number of measurements
	window_size = int(0.06*temps.shape[0])
	
	# you want it to be even. If it's odd, add 1
	if window_size % 2 != 0:
		window_size = window_size + 1
	
	# initialize empty list for averages
	# empty list
	averages = []
	
	# calculate the sliding window averages
	for i in range(window_size/2, (temps.shape[0] - window_size/2)):
		# calculate the mean in the window
		averages.append(np.mean(temps[i-(window_size/2):i+(window_size/2)]))
	
	# plotting time
	# plot the raw data first
	plt.plot(range(1,temps.shape[0]+1), temps, color='#3E4A89', alpha=0.6, linewidth = 0.60,label="raw temperature data")
	
	# then plot a thicker line for the smoothed average
	plt.plot(range(window_size/2, (temps.shape[0] - window_size/2)), averages, color='#3E4A89', linewidth = 2.0, label="sliding window average. window size of "+str(window_size))
	
	# axis labels
	plt.ylabel("temperature (F)")
	plt.xlabel("time (five-min intervals)")
	
	# place an annotation in the bottom left for IDing purposes
	plt.text(5,min(temps)-0.5,annotation)
	
	# make a legend and title
	plt.legend(loc='best', fancybox=True,prop={'size':10})
	plt.title("raw and smoothed temperature data")
	
	# save the figure as a pdf
	plt.savefig(str(name_of_brew) + "_temps.pdf",bbox_inches='tight',format='pdf')
	
	# clear the figure
	plt.clf()

def send_email(message, passw, graph = False):
        
	fromaddr = "lukesfermenter@gmail.com"
	toaddr = "lukereding@gmail.com"
	 
	msg = MIMEMultipart()
	 
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = "a message from your fermenter"
	 
	body = message
	msg.attach(MIMEText(body, 'plain'))
	
	# if sending a graph, attach it to the email:
	if graph == True:
		plot_temps(temps, name_of_brew)
		msg.attach(MIMEText(body, 'plain'))
		filename = str(name_of_brew) + "_temps.pdf"
		attachment = open(str(name_of_brew) + "_temps.pdf", "rb")
		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
		msg.attach(part)
	else:
		pass
	 
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(fromaddr, passw)
	text = msg.as_string()
	server.sendmail(fromaddr, toaddr, text)
	server.quit()
		
		

def my_job(temp,csvWriter,temps):

	try:
		# try grabbing to current temp and writing it to the csv file
		current_temp = read_temp()
		print current_temp
		temps.append(current_temp)
		csvWriter.writerow((current_temp, time.strftime("%d/%m/%Y"),time.strftime("%H:%M:%S")) )
	except: # send an email if you can't
		send_email("can't read the temperature")

	# now to regulate the temperature:
	if current_temp > (temp + 1):
		print "turning on the fridge"
		## turn on the power source
		io.output(power_pin, True)
		logging.info("temperature is " + str(current_temp))
		logging.info("turned on the mini fridge")
	elif current_temp < (temp - 1):
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
	
	# append the current temperature to the temperature list
	logging.info("length of temps: " + str(len(temps)))
	

def recordAndRegulateTemp(number_of_hours,temperature,csvWriter):
	sched = Scheduler()
	sched.start()
	job = sched.add_interval_job(my_job, minutes=5, args = [temperature,csvWriter,temps])

	start_time = time.time()
	while time.time() - start_time < (3600*int(number_of_hours)):
		text = "time left: " + str(round((3600*int(number_of_hours)) - (time.time()-start_time),0))+ " seconds\n"
		sys.stdout.write(text); sys.stdout.flush()
#		print "temp list: " + str(temps)
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
	
	with open('./mail.pass') as f:
		content = [x.strip('\n') for x in f.readlines()]
	password = content[0]
	
	try:
		name_of_brew = sys.argv[1]
	except:
		send_email("you didn't give your brew a name. I'm going to call it something stupid like 'defaultBrew'", password, graph = False)
		name_of_brew = "defaultBrew"
	
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
		send_email("seems like there's something wrong with how the program is attempting to interact with the temperature probe. the program is exiting", password, graph = False)
		sys.exit()

	# set up gpio pins to regulate fridge
	io.setmode(io.BCM)
	power_pin = 23 # might be different for you
	try:
		io.setup(power_pin,io.OUT)
		io.output(power_pin, False)
	except:
		send_email("check to make sure the relay is hooked up correctly", password, graph = False)

	# set up csv writing
	file = open(str(name_of_brew) + "_tempRecordings.csv", 'wb')
	writer = csv.writer(file)

	# set up logging
	logging.basicConfig(filename="./logs/" + str(name_of_brew) + "_brew.log",level=logging.DEBUG,format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')

	sched = Scheduler()
	sched.start()
	
	# set up empty list for internal processing
	# in the future: record target temp and time as a tuple here
	global temps
	temps = []
	
	# start email scheduler
	email_sched = Scheduler()
	email_sched.start()
	text = "it's been twelve hours. here are the latest temperature readings from your new brew"
	email_job = sched.add_interval_job(send_email,hours=8,args = [text, password, True])
	
	# this is the heart of the program:
	# send email to let me know I'm brewing
	send_email("starting brew log.", password, graph=False)
	
	# get list of temps:
	list_of_temps = sys.argv[2::2]
	# get lengths of time for each of those temperatures
	list_of_times = sys.argv[3::2]
	
	# convert to ints
	list_of_temps = map(int,list_of_temps)
	list_of_times = map(int, list_of_times)
	
	print "list of temps"
	print list_of_temps
	print "list of times"
	print list_of_times
	
	for i in range(0,len(list_of_times)):
		send_email("changing temperature to " + str(list_of_temps[i]) + " for " + str(list_of_times[i]) + " hours.", password, graph = False)
		recordAndRegulateTemp(list_of_times[i],list_of_temps[i],writer)
	
	print "program done. fermenter shutting down."
	send_email("ending. fermenter is shutting off", password, graph=True)
	email_sched.unschedule_job(send_email)
	io.output(power_pin, False)
