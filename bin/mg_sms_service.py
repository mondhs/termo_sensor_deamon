#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys,os
import time  
import datetime 
import atexit
import stat



# Deafults
LOG_FILENAME = "/tmp/mg_sms_service.log"
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

FIFO = '/var/local/mg_termo_service/message.fifo'
READ_PIPE_EVERY_MIN_IN_SEC = 1#5 * 60
PHONE_NUMBER = "+37065042124"


def sendSms(message):
	logger.info("Send SMS with message: " + message + "; len: " + str(len(message)))
	if len(message) > 150:
		raise error('Message too long ') 
	sm = gammu.StateMachine()
	sm.ReadConfig()
	sm.Init()
	message = {
	    'Text': message,
	    'SMSC': {'Location': 1},
	    'Number': PHONE_NUMBER,
	}
	#sm.SendSMS(message)
	logger.info("Send SMS successfuly")



@atexit.register
def cleanup():
    try:
        os.unlink(FIFO)
    except:
        pass

def readerator(fd):

    """This reads data in a tight loop from a non-blocking file-descriptor.
    When data is found it is yielded. A short sleep is added when no
    data is available."""

    while True:
        data = os.read(fd, 150)
        if not data:
            time.sleep(READ_PIPE_EVERY_MIN_IN_SEC)
        else:
            yield data

def pipeWatcher():    
    os.mknod(FIFO, 0666 | stat.S_IFIFO)
    print("The open() call will block until data is put into the FIFO.")
    fifo_in = os.open(FIFO, os.O_RDONLY)
    print("The open() call has unblocked.")
    
    while True:
        for cc in readerator(fifo_in):
            print(cc)
            sendSms(cc)


os.system(os.environ['HOME'] + "/bin/gammu_unlock.sh")



logger.info("start sms service")

# Loop forever, doing something useful hopefully:
while True:
	try:
		pipeWatcher()
	except (KeyboardInterrupt, SystemExit):
		break

logger.info("stoping service")
