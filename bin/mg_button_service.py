#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys,os
import time  # this is only being used as part of the example
import datetime 
import RPi.GPIO as GPIO



# Deafults
LOG_FILENAME = "/tmp/mg_button_service.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="MG temperature tracking service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
	LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

ALARM_FILE_NAME = "/var/local/mg_termo_service/alarm.txt"
NOTIFY_FIFO = '/var/local/mg_termo_service/message.fifo'
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
ROWS_IN_FILE = 100
NOTIFY_EVERY_SEC = 4# * 3600


GPIO.setmode(GPIO.BCM)

GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def sendSms(message):
	logger.info("Send SMS with message: " + message + "; len: " + str(len(message)))
	if stat.S_ISFIFO(os.stat(NOTIFY_FIFO).st_mode):
        with open(NOTIFY_FIFO, 'a') as fifo:
            fifo.write(message)
	    logger.info("Send SMS successfuly")
	else:
	    logger.info("NOT Send SMS. service not running")

# Define a threaded callback function to run in another thread when events are detected
def my_callback(channel):
    if GPIO.input(23):     # if port 23 == 1
        logger.info("Rising edge detected on 23")
        print "Alarm triggered"
        eventDate = datetime.datetime.now()
        lastNotified = datetime.datetime.now() - datetime.timedelta(weeks=4)
        with open(ALARM_FILE_NAME,"r") as f:
    	    data = f.readline()
            lastNotified = datetime.datetime.strptime(data, DATE_FORMAT)
            
	    delta = (eventDate - lastNotified).total_seconds()
        logger.info("delta.total_seconds(): " + str(delta) + "; started: " + lastNotified.strftime("%Y%m%d") + "; event: " + eventDate.strftime("%Y%m%d")  )
        if delta > NOTIFY_EVERY_SEC:
            sendSms("{}; Alarmas suaktyvintas.\n".format(eventDate.strftime(DATE_FORMAT)))
            with open(ALARM_FILE_NAME, 'w') as f:
                f.write(datetime.datetime.now().strftime(DATE_FORMAT))
    else:                  # if port 23 != 1
        logger.info("falling edge detected on 23")
    	pass


GPIO.add_event_detect(23, GPIO.BOTH, callback=my_callback, bouncetime=500)

logger.info("start button service")

lastNotified = datetime.datetime.now() - datetime.timedelta(weeks=4)
with open(ALARM_FILE_NAME, 'w') as f:
    f.write(datetime.datetime.now().strftime(DATE_FORMAT))



try:
    while True:
        #input_state = GPIO.input(23)
        #if input_state == False:
            #print('Klavisas nuspaustas')
            #os.system("/root/temperatura_sms.sh")
        time.sleep(30)
finally:                   # this block will run no matter how the try block exits
    GPIO.cleanup()         # clean up after yourself



logger.info("stoping service")
