# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import task

import json
import logging
import sys
import time
from pprint import pprint

from django.shortcuts import get_object_or_404
from requestsHandler.models import UserConfig

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields, find_pipline_id
from utils import one_by_one, zero_department, not_chosen, ending_statuses, weekdays
from utils import get_config_forms
from requests_logger import log_request, log_exception, log_info, Message_type, \
    get_current_function, log_error, unknown_username

def eject_settings(post_data, get_data, ip=None):   
    try:
        if 'public_hash' in get_data:
            user_cfg = UserConfig.objects.get(public_hash=get_data['public_hash'])
        elif 'private_hash' in get_data:
            user_cfg = UserConfig.objects.get(private_hash=get_data['private_hash'])
        else:
            return
    except UserConfig.DoesNotExist:
        log_error('User cfg was not found!', '__no_name__', get_current_function(), post_data)
        return
    
    username = user_cfg.user.username
    log_info('Got data', user_cfg.user.username, get_current_function(), post_data)
    
    if not user_cfg.user.is_active:
        log_info('User is not active ', user_cfg.user.username, \
            get_current_function(), user_cfg.account_rights)
        return
    
    if not 'form_type' in get_data or not get_data['form_type'] in user_cfg.config:
        message = 'No form type in config %s' % user_cfg.user.username
        raise AmoException(message, {})
    form_type = get_data['form_type']
    
    if not 'form' in get_data or not get_data['form'] in user_cfg.config[form_type]:
        message = 'No form in config %s' % user_cfg.user.username
        raise AmoException(message, {})
    requested_form = get_data['form']
    
    api = AmoIntegr(user_cfg)
    settings = user_cfg.config[form_type][requested_form]
    
    data_to_send, generate_tasks_for_rec, department_id, internal_kwargs = conform_fields(
        post_data, settings, user_cfg.account_rights, ip)
            
    if 'distribution_settings' in settings and settings['distribution_settings']:
        internal_kwargs['distribution_settings'] = \
           settings['distribution_settings']
           
    if 'another_distribution' in settings and 'another_dist_type' in settings:
        another_distribution = settings['another_distribution']
        type_another_form = settings['another_dist_type']
        
        if another_distribution != not_chosen and \
            (another_distribution != requested_form or type_another_form != form_type) and \
            another_distribution and type_another_form and \
            type_another_form in user_cfg.config and \
            another_distribution in user_cfg.config[type_another_form]:
                
            another_conform = user_cfg.config[type_another_form][another_distribution]
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
            form_type = type_another_form
            
    return user_cfg, api, data_to_send, requested_form, form_type, department_id, \
        generate_tasks_for_rec, internal_kwargs

retry_coef = 5
@task(ignore_result=True)
def send_data_to_amo(post_data, get_data, ip=None):
    try:
        username=unknown_username
        user_cfg, api, data_to_send, requested_form, form_type, department_id, \
            generate_tasks_for_rec, internal_kwargs = eject_settings(post_data, get_data, ip)
        username = user_cfg.user.username
        
        result = api.send_order_data(
            contact_data = data_to_send['contact_data'], 
            lead_data = data_to_send['lead_data'], 
            company_data = data_to_send['company_data'], 
            form = requested_form,
            form_type = form_type,
            department_id = department_id, 
            generate_tasks_for_rec = generate_tasks_for_rec,
            **internal_kwargs
        )    
        
        user_cfg.save()
        
        return result
        
    except AmoException as e:
        context = e.context
        log_exception('', username, get_current_function(), context)
        if e.resend:
            send_data_to_amo.retry(exc=e, countdown=retry_coef * send_data_to_amo.request.retries) 
            # send_data_to_amo.retry(exc=e, countdown=retry_coef) 

@task(ignore_result=True)
def rotate_user(post_data, get_data, ip=None):
    try:
        username=unknown_username
        user_cfg, api, data_to_send, requested_form, form_type, department_id, \
            generate_tasks_for_rec, internal_kwargs = eject_settings(post_data, get_data, ip)
        username = user_cfg.user.username
        
        if 'distribution_settings' in internal_kwargs and internal_kwargs['distribution_settings']:
            responsible_user_id = api.rotate_user(department_id, requested_form, form_type, \
                distribution_settings=internal_kwargs['distribution_settings'])
        else:
            responsible_user_id = api.rotate_user(department_id, requested_form, form_type)
        
        api.update_entity(
            'contacts', 
            post_data['id'], 
            translate = False,
            call = True,
            updated_at = time.time(),
            responsible_user_id = responsible_user_id
        )
        
        count_down = 4
        tasks = []
        while count_down > 0 and not tasks:
            time.sleep(0.1)
            tasks = api.get_entity(
                'tasks',
                element_id=post_data['id']
            )['_embedded']['items']
            count_down -= 1
        
        for task in tasks:
            result = api.update_task(
                task_id = task['id'], 
                updated_at = time.time(),
                text = task['text'],
                call=True,
                responsible_user_id = responsible_user_id
            )
        
        user_cfg.save()
        
        return post_data, get_data, ip
        
    except AmoException as e:
        context = e.context
        log_exception('', username, get_current_function(), context)
        if e.resend:
            send_data_to_amo.retry(exc=e, countdown=retry_coef * send_data_to_amo.request.retries) 
            # send_data_to_amo.retry(exc=e, countdown=retry_coef) 