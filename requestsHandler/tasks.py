# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import task

import json
import logging
import sys
from pprint import pprint

from django.shortcuts import get_object_or_404
from requestsHandler.models import UserConfig

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields, find_pipline_id
from utils import one_by_one, zero_department, not_chosen, ening_statuses, weekdays
from utils import get_config_forms
from requests_logger import log_request, log_exception, log_info, Message_type, \
    get_current_function, log_error
    
retry_coef = 60

@task()
def send_data_to_amo(username, post_data, get_data):
    try:
        try:
            user_cfg = UserConfig.objects.get(public_hash=get_data['public_hash'])
        except UserConfig.DoesNotExist:
            log_error('User cfg was not found!', '__no_name__', get_current_function(), post_data)
            return
 
        log_info('Got data ', user_cfg.user.username, get_current_function(), post_data)
        
        if not user_cfg.user.is_active:
            log_info('User is not active ', user_cfg.user.username, \
                get_current_function(), user_cfg.account_rights)
            log_error('User is not active!', user_cfg.user.username, get_current_function(), post_data)
        
        if not get_data['form'] in user_cfg.config:
            message = 'No form %s in config %s' % (get_data['form'], user_cfg.user.username)
            log_error(message, user_cfg.user.username, get_current_function(), post_data)
        
        requested_form = get_data['form']
        
        api = AmoIntegr(user_cfg)

        data_to_send, generate_tasks_for_rec, department_id, internal_kwargs = conform_fields(
            post_data, user_cfg.config[requested_form], user_cfg.account_rights)
                
        if 'distribution_settings' in user_cfg.config[requested_form] and \
            user_cfg.config[requested_form]['distribution_settings']:
            internal_kwargs['distribution_settings'] = \
               user_cfg.config[requested_form]['distribution_settings']
               
        if 'another_distribution' in user_cfg.config[requested_form]:
            another_distribution = user_cfg.config[requested_form]['another_distribution']
            if another_distribution != not_chosen and another_distribution != requested_form:
                another_conform = user_cfg.config[another_distribution]
                department_id = -1
                if 'department_id' in another_conform and \
                    another_conform['department_id'] != not_chosen:
                    department_id = another_conform['department_id']
                internal_kwargs['responsible_user_id'] = one_by_one
                if 'responsible_user_id' in another_conform and \
                    another_conform['responsible_user_id'] != one_by_one:
                    internal_kwargs['responsible_user_id'] = another_conform['responsible_user_id']
                internal_kwargs['distribution_settings'] = []
                if 'distribution_settings' in another_conform and \
                    another_conform['distribution_settings']:
                    internal_kwargs['distribution_settings'] = another_conform['distribution_settings']
                requested_form = another_distribution
        
        reslut = api.send_order_data(
            contact_data = data_to_send['contact_data'], 
            lead_data = data_to_send['lead_data'], 
            company_data = data_to_send['company_data'], 
            form = requested_form,
            department_id = department_id, 
            generate_tasks_for_rec = generate_tasks_for_rec,
            **internal_kwargs
        )    
        
        user_cfg.save()
        
    except AmoException as e:
        context = e.context
        log_exception('', username, get_current_function(), context)
        send_data_to_amo.retry(exc=e, countdown=retry_coef * send_data_to_amo.request.retries) 
        

