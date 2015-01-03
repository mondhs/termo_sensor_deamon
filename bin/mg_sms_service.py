#!/usr/bin/env python

import logging
import logging.handlers
import argparse
import sys,os
import time  
import datetime 
import atexit
import stat
import gammu



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

NOTIFY_FIFO = '/var/local/mg_termo_service/message.fifo'
READ_PIPE_EVERY_SEC = 1 * 60
PHONE_NUMBER = "+37065042124"


def sendSms(message_content):
    message_to_send = message_content
    logger.info("Send SMS with message: {0}; len: {1}".format(message_to_send, str(len(message_to_send))))
    if len(message_to_send) > 150:
        message_to_send = message_to_send[:146]+"..."
        logger.info("shorter message_to_send {0}".format(message_to_send))
    sm = gammu.StateMachine()
    sm.ReadConfig()
    sm.Init()
    smsMessage = {
        'Text': message_to_send,
        'SMSC': {'Location': 1},
        'Number': PHONE_NUMBER,
    }
    #sm.SendSMS(smsMessage)
    logger.info("Send SMS successfuly")
    return message_to_send



@atexit.register
def cleanup():
    try:
        os.unlink(NOTIFY_FIFO)
    except Exception, e:
        logger.exception(e)


def pipeWatcher():
    fifo = open(NOTIFY_FIFO, "r")
    allLines = fifo.readlines()
    try:
        sentMessage = sendSms(",".join(allLines))
    except Exception, e:
        logger.exception(e)
    fifo.close()

#os.system(os.environ['HOME'] + "/bin/gammu_unlock.sh")

try:
    if stat.S_ISFIFO(os.stat(NOTIFY_FIFO).st_mode):
        cleanup()
except Exception, e:    
    logger.exception(e)
try:
    os.mkfifo(NOTIFY_FIFO, 0666)
except Exception, e:    
    logger.exception(e)

logger.info("start sms service. phone %s every %i sec", PHONE_NUMBER, READ_PIPE_EVERY_SEC)

while True:
    try:
        pipeWatcher()
        time.sleep(READ_PIPE_EVERY_SEC)
    except (KeyboardInterrupt, SystemExit):
        break

logger.info("stoping service")
