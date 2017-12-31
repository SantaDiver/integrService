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
logger_name = 'requests_logger'

from enum import Enum
class Message_type(Enum):
    INBOUND = 'INBOUND',
    OUTBOUND = 'OUTBOUND',
    FUNCTION = 'FUNCTION',
    EXCEPTION = 'EXCEPTION',
    INFO = 'INFO'

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
            logger = setup_logger(
                name = logger_name, 
                log_file = logging_directory + request.user.username + '.log', 
                level = logging.INFO
            )
            message = '%s log_request at %s ' % (message_type, func.__name__)
            if request.method == 'GET' and request.GET:
                message += 'GET params ' + json.dumps(request.GET, indent=2, \
                    sort_keys=True, ensure_ascii=False)
            if request.method == 'POST' and request.POST:
                message += 'POST params ' + json.dumps(request.POST, indent=2, \
                    sort_keys=True, ensure_ascii=False)
            if request.body.decode('utf-8'):
                try:
                    message += 'BODY ' + json.dumps(json.loads(request.body.decode('utf-8')), \
                        indent=2, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    message += 'BODY ' + request.body.decode('utf-8')
            logger.info(message)
            
            # Function call
            result = func(request)
            
            # After function
            logger = setup_logger(
                name = logger_name, 
                log_file = logging_directory + request.user.username + '.log', 
                level = logging.INFO
            )
            logger.info('Request successfully handled!\n')
            
            return result
        return func_wrapper
    return func_decorator
    
def log_exception(username, context):
    logger = setup_logger(
        name = logger_name, 
        log_file = logging_directory + username + '.log', 
        level = logging.ERROR
    )
    logger.exception('%s log_exception ' % Message_type.EXCEPTION + \
        json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False))
    
    exception_context = context
    client.captureException()
    
def log_info(message, username, at, context):
    logger = setup_logger(
        name = logger_name, 
        log_file = logging_directory + username + '.log', 
        level = logging.INFO
    )
    logger.info('%s %s log_info at %s' % (Message_type.INFO, message, at) + \
        json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False))
    
    exception_context = context
    client.captureException()
    

import inspect 
def get_current_function():
    return inspect.stack()[1][3]
    