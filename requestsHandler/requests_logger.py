from pprint import pprint
import logging
import json
from logging.handlers import RotatingFileHandler
from raven.contrib.django.raven_compat.models import client
from functools import wraps

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logging_directory = './requestsHandler/logs/'

import os
directory = os.path.dirname(logging_directory)
try:
    os.stat(directory)
except:
    os.mkdir(directory)

max_bytes = 50*1024*1024
backup_count = 2
logger_name = 'requests_logger_'

from enum import Enum
class Message_type(Enum):
    INBOUND = 'INBOUND',
    OUTBOUND = 'OUTBOUND',
    FUNCTION = 'FUNCTION'
    
class Message_level(Enum):
    EXCEPTION = 'EXCEPTION',
    INFO = 'INFO',
    ERROR = 'ERROR'

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers == []:
        handler = RotatingFileHandler(log_file, mode='a', maxBytes=max_bytes, 
                                 backupCount=backup_count, encoding=None, delay=0)       
        handler.setFormatter(formatter)

        logger.addHandler(handler)
    
    return logger
    
def log_request(message_type):
    def func_decorator(func):
        @wraps(func)
        def func_wrapper(request):
            # Before function
            
            username = request.user.username
            at = func.__name__
           
            message = '%s log_request' % message_type
            
            context = {}
            if request.method == 'GET' and request.GET:
                context['GET'] = request.GET
            if request.method == 'POST' and request.POST:
                context['POST'] = request.POST
            if request.body.decode('utf-8'):
                try:
                    context['BODY'] = json.loads(request.body.decode('utf-8'))
                except ValueError:
                    context['BODY'] = request.body.decode('utf-8')
                    
            log_info(message, username, at, context)
            
            # Function call
            result = func(request)
            
            # After function
            log_info('Request successfully handled!', username, at, {})
            
            return result
        return func_wrapper
    return func_decorator
    
def log_message(message_level, message, username, at, context):
    level = {
       Message_level.EXCEPTION : logging.ERROR,
       Message_level.ERROR : logging.ERROR,
       Message_level.INFO : logging.INFO,
    }[message_level]
    
    logger = setup_logger(
        name = logger_name + username, 
        log_file = logging_directory + username + '.log', 
        level = level
    )
    
    if message_level == Message_level.EXCEPTION:
        logger.exception('%s %s log_exception at %s ' % (Message_level.EXCEPTION, \
            message, at) + json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False))
        
        client.captureException() 
        
    elif message_level == Message_level.INFO:
        logger.info('%s %s log_info at %s ' % (Message_level.INFO, message, at) + \
            json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False))
            
    elif message_level == Message_level.ERROR:
        logger.error('%s %s log_error at %s ' % (Message_level.ERROR, message, at) + \
            json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False))
    
def log_exception(message, username, at, context):
    log_message(Message_level.EXCEPTION, message, username, at, context)

def log_info(message, username, at, context):
    log_message(Message_level.INFO, message, username, at, context)

def log_error(message, username, at, context):
    log_message(Message_level.ERROR, message, username, at, context)


import inspect 
def get_current_function():
    try:
        return inspect.stack()[1][3]
    except:
        return 'not knonwn'
    