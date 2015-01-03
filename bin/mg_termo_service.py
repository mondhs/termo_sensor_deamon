#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys,os, stat
import time  # this is only being used as part of the example
from w1thermsensor import W1ThermSensor
import datetime 




# Deafults
LOG_FILENAME = "/tmp/mg_termo_service.log"
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

FILE_NAME = "/var/local/mg_termo_service/data_archive.csv"
NOTIFY_FIFO = '/var/local/mg_termo_service/message.fifo'
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
ROWS_IN_FILE = 100
NOTIFY_EVERY_SEC = 4 * 3600
READ_SENSOR_EVERY_SEC = 5 * 60

def initReadings():
	readingIndex = 0
	scriptStarted = datetime.datetime.now()
	try:
		lastReadings = []
		firstReadings = []
		with open(FILE_NAME) as inFile:
			allReadings = inFile.readlines()
			firstReadings = allReadings[0].split(",")
        		lastReadings = allReadings[-1].split(",")
	 	lastNumber = lastReadings[0].strip()

        	scriptStarted = datetime.datetime.strptime(firstReadings[2].strip(), DATE_FORMAT)
	        readingIndex = int(lastNumber)
	except (IndexError,IOError):
        	logger.info("start service fresh ")
	return readingIndex, scriptStarted

def sendSms(message):
	logger.info("Send SMS with message: " + message + "; len: " + str(len(message)))
	if stat.S_ISFIFO(os.stat(NOTIFY_FIFO).st_mode):
        with open(NOTIFY_FIFO, 'a') as fifo:
            fifo.write(message)
	    logger.info("Send SMS successfuly")
	else:
	    logger.info("NOT Send SMS. service not running")



def reportStatus(eventDate, temperature):
	message = "Dabar pas mane {}. temp1: {}".format(eventDate.strftime(DATE_FORMAT), str(temperature))
	sendSms(message)
	
def logData(index, temperature, eventDate, lastNotified):
	dateStr = eventDate.strftime(DATE_FORMAT)
	delta = (eventDate - lastNotified).total_seconds()
	logger.info("delta.total_seconds(): " + str(delta) + "; started: " + lastNotified.strftime("%Y%m%d") + "; event: " + eventDate.strftime("%Y%m%d") + "; report? " + str(delta > NOTIFY_EVERY_SEC) )
	logger.info("index :" + str(index) + "; mod: " + str(index % ROWS_IN_FILE) +  "; div: " + str(index/ROWS_IN_FILE))
	if index % ROWS_IN_FILE == 0:
		moveTo = FILE_NAME+str(index/ROWS_IN_FILE)
		logger.info("Move file to" + moveTo)
		os.rename(FILE_NAME, moveTo)	
	if delta > NOTIFY_EVERY_SEC:
		reportStatus(eventDate, temperature)
		lastNotified=eventDate
	message = "{}, {}, {}\n".format(str(index), str(temperature), dateStr)
	with open(FILE_NAME, "a") as outFile:
		outFile.write(message)
	return lastNotified

def readSensors(readingIndex, lastNotified):
	temperature_in_celsius = sensor.get_temperature()
	nowDate = datetime.datetime.now()
	lastNotified = logData(readingIndex, temperature_in_celsius, nowDate, lastNotified)
	readingIndex += 1
	return readingIndex, lastNotified

os.system(os.environ['HOME'] + "/bin/gammu_unlock.sh")

sensor = W1ThermSensor()

readingIndex, scriptStarted = initReadings()

lastNotified = datetime.datetime.now() - datetime.timedelta(weeks=4)


logger.info("start service: " + str(readingIndex) + "; script started: " + scriptStarted.strftime(DATE_FORMAT))

readingIndex += 1
# Loop forever, doing something useful hopefully:
while True:
	try:
		readingIndex, lastNotified = readSensors(readingIndex, lastNotified)
		time.sleep(READ_SENSOR_EVERY_SEC)
	except (KeyboardInterrupt, SystemExit):
		break

logger.info("stoping service")
