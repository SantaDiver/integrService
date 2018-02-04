import json
import logging
import sys
from pprint import pprint
import time
import logging

from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.http import Http404
from requestsHandler.models import UserConfig
from django.contrib.auth.models import User

from dadata.plugins.django import DjangoDaDataClient
from raven.contrib.django.raven_compat.models import client
from ipware import get_client_ip
from celery import chain

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields, find_pipline_id, unflatten
from utils import one_by_one, zero_department, not_chosen, ending_statuses, weekdays
from utils import get_config_forms, config_types
from requests_logger import log_request, log_exception, log_info, Message_type, \
    get_current_function
from tasks import send_data_to_amo, rotate_user

# TODO: JIVOsite
# TODO: Change another distribution when delete form
# TODO: tags in email/jivo etc
# TODO: scan for phone in email
# TODO: test context passing to sentry
# TODO: russian form names
# TODO: start using React :)

logger = logging.getLogger(__name__)

@csrf_exempt
def siteHandler(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Waiting for POST request')
    if not 'public_hash' in request.GET:
        return HttpResponseBadRequest('Public hash field is required')
    if not 'form' in request.GET:
        return HttpResponseBadRequest('Form field is required')
    
    get_data = request.GET.copy()
    get_data['form_type'] = 'site_forms'
    ip, is_routable = get_client_ip(request)
    send_data_to_amo.delay(request.POST, get_data, ip)
    
    # send_data_to_amo(request.POST, get_data, ip)
        
    return HttpResponse('OK')

@csrf_exempt
def emailHandler(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Waiting for POST request')
    if not 'private_hash' in request.GET:
        return HttpResponseBadRequest('Public hash field is required')
    if not 'form' in request.GET:
        return HttpResponseBadRequest('Form field is required')
        
    get_data = request.GET.copy()
    get_data['form_type'] = 'email'
    
    post_data = request.POST.copy()
    if 'from' in post_data:
        splited = post_data['from'].split('<')
        if len(splited) == 2:
            name = splited[0]
            email = splited[1][:-1]
            
            post_data['from.name'] = name
            post_data['from.email'] = email
        
    
    # send_data_to_amo.delay(post_data, get_data)
    send_data_to_amo(post_data, get_data)
    
    return HttpResponse('OK')
    
# Form name should be equal to phone number called
@csrf_exempt
def onpbxHandler(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Waiting for POST request')
    if not 'private_hash' in request.GET:
        return HttpResponseBadRequest('Public hash field is required')
    if not 'form' in request.GET:
        return HttpResponseBadRequest('Form field is required')
        
    get_data = request.GET.copy()
    get_data['form_type'] = 'onpbx'
    
    post_data = unflatten(request.POST)
    
    if 'contact' in post_data and 'add' in post_data['contact']:
        for key, c in post_data['contact']['add'].items():
            splited_name = c['name'].split(' ')
            if len(splited_name) > 2:
                c['phone'] = splited_name[1]
                called_phone = splited_name[2].split('-')[0][1:]
                if called_phone==str(get_data['form']):
                    if splited_name[0] == 'Пропущенный':
                        chain(
                            rotate_user(c, get_data, None), 
                            send_data_to_amo(c, get_data, None)
                        ).apply_async()
                        # rotate_user(c, get_data, None)
                        # send_data_to_amo(c, get_data, None)
                    elif splited_name[0] == 'Входящий':
                        send_data_to_amo.delay(c, get_data, None)
                        # send_data_to_amo(c, get_data, None)
    
    return HttpResponse('OK')
    

@login_required
@log_request(Message_type.INBOUND)
def configurator(request):
    try:
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        request_path = request.path[1:]
        
        valid_path = False
        if not request_path:
            valid_path = True
        elif request_path == 'accesses':
            valid_path = True
        else:
            splited_path = request_path.split('/')
            if len(splited_path) == 2:
                if splited_path[0] in config and splited_path[1] in config[splited_path[0]]:
                    valid_path = True
                elif splited_path[0] in config and splited_path[1] == 'add_form':
                    valid_path = True
                
        if valid_path:
            return render(request, 'requestsHandler/configurator.html', {
                'config':config, 
                'username': user_cfg.user.username
            })
        else:
            raise Http404('Path %s wasnt found' % request.path[1:])
            
    except AmoException as e:
        context = e.context
        log_exception('', request.user.username, get_current_function(), context)
        return HttpResponseBadRequest()
    

@login_required
@log_request(Message_type.INBOUND)
def setConfig(request):
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest('Waiting for POST request')
            
        got_config = json.loads(request.body.decode('utf-8'))
        if not 'form' in got_config:
            return HttpResponseBadRequest('Form field is required')
        
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        log_info('Config before updateing', user_cfg.user.username, get_current_function(), user_cfg.config)
        
        first_lvl_data = ['user', 'subdomain', 'hash']
        for field in first_lvl_data:
            if field in got_config:
                if field == 'time_to_complete_rec_task':
                    got_config[field] *= 60
                config[field] = got_config[field]
                
        if got_config['form'] == 'accesses':
            user_cfg.save()
            return HttpResponse(200)
        
        if not 'config_type' in got_config or not got_config['config_type'] in \
            config or not got_config['form'] in config[got_config['config_type']]:
            return HttpResponseNotFound('No form %s in config %s' % \
                (got_config['form'], user_cfg.user.username))
                
        form = got_config['form']
        config_type = got_config['config_type']
        settings = config[config_type][form]
        
        if not 'fields_to_check_dups' in settings:
            settings['fields_to_check_dups'] = {}
        if 'contact_fields_to_check_dups' in got_config:
            settings['fields_to_check_dups']['contacts'] = \
                [field['field'] for field in got_config['contact_fields_to_check_dups']]
        if 'company_fields_to_check_dups' in got_config:
            settings['fields_to_check_dups']['companies'] = \
                [field['field'] for field in got_config['company_fields_to_check_dups']]
        
        additional_params = ['rec_lead_task_text', 'time_to_complete_rec_task', \
            'generate_tasks_for_rec', 'tag_for_rec', 'exceptions']
        for param in additional_params:
            if param in got_config:
                if param == 'time_to_complete_rec_task':
                    got_config[param] *= 60
                settings[param] = got_config[param]
        
        if 'another_distribution' in got_config:
            splited_distr = got_config['another_distribution'].split('/')
            if len(splited_distr) == 2:
                settings['another_dist_type'] = splited_distr[0]
                settings['another_distribution'] = splited_distr[1]
            else:
                settings['another_distribution'] = not_chosen
        
        if '_embedded' in user_cfg.cache:
            if 'distribution_settings' in got_config:
                for idx, distr_settings in enumerate(got_config['distribution_settings']):
                    distr_user_id = next((user_id for user_id, user in user_cfg.cache \
                        ['_embedded']['users'].items() if user['name'] == distr_settings['user']), None)
                    got_config['distribution_settings'][idx]['user'] = distr_user_id
                
                if not 'distribution_settings' in settings:
                    settings['distribution_settings'] = got_config['distribution_settings']
                else:
                    pairs = zip(settings['distribution_settings'], got_config['distribution_settings'])
                    if any(x != y for x, y in pairs):
                        user_cfg.last_user_cache[config_type][form] = {}
                    settings['distribution_settings'] = got_config['distribution_settings']
            
            if 'responsible_user' in got_config:
                if got_config['responsible_user'] == one_by_one:
                    settings['responsible_user_id'] = one_by_one
                else:
                    for user_id, user in user_cfg.cache['_embedded']['users'].items():
                        if user['name'] == got_config['responsible_user']:
                             settings['responsible_user_id'] = user_id
                             
            if 'department' in got_config:
                if got_config['department'] == zero_department:
                    settings['department_id'] = 0
                elif got_config['department'] == not_chosen:
                    settings['department_id'] = not_chosen
                else:
                    for group_id, group in user_cfg.cache['_embedded']['groups'].items():
                        if group['name'] == got_config['department']:
                             settings['department_id'] = int(group_id)
            
            if not 'pipelines' in settings:
                settings['pipelines'] = {}
            if 'status_for_new' in got_config:
                settings['pipelines']['status_for_new'] = \
                    find_pipline_id(user_cfg.cache['_embedded']['pipelines'], got_config['status_for_new'])
            if 'status_for_rec' in got_config:
                settings['pipelines']['status_for_rec'] = \
                    find_pipline_id(user_cfg.cache['_embedded']['pipelines'], got_config['status_for_rec'])
                    
            if 'contact_fields' in got_config:
                settings['contact_data'] = {}
                for field in got_config['contact_fields']:
                    settings['contact_data'][field['amoCRM']] = field['site']
                    
            if 'company_fields' in got_config:
                settings['company_data'] = {}
                for field in got_config['company_fields']:
                    settings['company_data'][field['amoCRM']] = field['site']
                    
            if 'lead_fields' in got_config:
                settings['lead_data'] = {}
                for field in got_config['lead_fields']:
                    settings['lead_data'][field['amoCRM']] = field['site']
                
                
        user_cfg.save()
        
        log_info('Updated config', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
        
    except AmoException as e:
        context = e.context
        log_exception('', request.user.username, get_current_function(), context)
        return HttpResponseBadRequest()
    
@login_required 
@log_request(Message_type.INBOUND)
def getConfig(request):
    try:
        if request.method != 'GET':
            return HttpResponseBadRequest('Waiting for GET request')
        if not 'hash' in request.GET:
            return HttpResponseBadRequest('Hash parameter needed!')
        if not 'form_type' in request.GET:
            return HttpResponseBadRequest('Form type parameter needed!')
            
        requested_form = request.GET['hash']
        form_type = request.GET['form_type']
        
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        
        config = user_cfg.config
        try:
            api = AmoIntegr(user_cfg)
            api.update_cache()
            user_cfg.save()
            config['valid_amo'] = True
        except AmoException as e:
            config['valid_amo'] = False
        
        if requested_form != 'accesses':
            if not form_type in config:
                return HttpResponseNotFound('No type %s in config %s' % \
                    (form_type, user_cfg.user.username))
            if not requested_form in config[form_type]:
                return HttpResponseNotFound('No form %s in config %s' % \
                    (requested_form, user_cfg.user.username))
        
        if '_embedded' in user_cfg.cache and requested_form != 'accesses':
            config['forms'] = []
            for t in config_types:
                if t in config:
                    config['forms'] += [t+'/'+form_name for form_name in config[t]]
            config['forms'].append(not_chosen)
                
            settings = config[form_type][requested_form]
            
            if 'another_distribution' in settings and 'another_dist_type' in settings and \
                settings['another_dist_type'] in config and settings['another_distribution'] \
                in config[settings['another_dist_type']]:
                    
                config['chosen_distr'] = settings['another_dist_type']+'/'+settings['another_distribution']
            else:
                config['chosen_distr'] = not_chosen
            
            def RepresentsInt(s):
                try: 
                    int(s)
                    return True
                except ValueError:
                    return False
                
            config['allowed_fields'] = {}
            config['allowed_statuses'] = []
            
            if not 'fields_to_check_dups' in settings:
                settings['fields_to_check_dups'] = {}
            
            additional_field_options = ['name', 'default_name', 'tags']
            contact_field_options = [field for field in user_cfg.fields_cache \
                ['contacts'] if not RepresentsInt(field)]
            contact_field_options += additional_field_options
            
            company_field_options = [field for field in user_cfg.fields_cache \
                ['companies'] if not RepresentsInt(field)]
            company_field_options += additional_field_options
            
            lead_field_options = [field for field in user_cfg.fields_cache \
                ['leads'] if not RepresentsInt(field)]
            lead_field_options += additional_field_options
            
            config['allowed_fields'] = {
                'contacts' : contact_field_options,
                'companies' : company_field_options,
                'leads' : lead_field_options
            }
            
            config['allowed_users'] = [user['name'] for user_id, user in \
                user_cfg.cache['_embedded']['users'].items() if not user['is_free'] \
                and user['is_active']]
            config['allowed_users'].append(one_by_one)
            
            for pipeline_id, pipeline in user_cfg.cache['_embedded']['pipelines'].items():
                for status_id, status in pipeline['statuses'].items():
                    if not int(status_id) in ending_statuses:
                        config['allowed_statuses'].append(pipeline['name']+'/'+status['name'])
            
            if 'responsible_user_id' in settings and settings['responsible_user_id'] != one_by_one:
                config['default_user'] = [user['name'] for user_id, user in 
                    user_cfg.cache['_embedded']['users'].items() if 
                    int(user_id) == int(settings['responsible_user_id'])][0]
            else:
                config['default_user'] = one_by_one
                
            if user_cfg.cache['_embedded']['groups']:
                config['allowed_departments'] = [group['name'] for group_id, group in 
                    user_cfg.cache['_embedded']['groups'].items()]
            else:
                config['allowed_departments'] = []
            config['allowed_departments'].append(zero_department)
            config['allowed_departments'].append(not_chosen)
            
            config['default_department'] = not_chosen
            if 'department_id' in settings:
                if settings['department_id'] != 0 and settings['department_id'] != not_chosen:
                    config['default_department'] = [group['name'] for group_id, group in 
                    user_cfg.cache['_embedded']['groups'].items() if 
                        int(group_id) == int(settings['department_id'])][0]
                elif settings['department_id'] == 0:
                    config['default_department'] = zero_department
                
            if 'pipelines' in settings:
                for pipeline_id, pipeline in user_cfg.cache['_embedded']['pipelines'].items():
                    for status_id, status in pipeline['statuses'].items():
                        if 'status_for_new' in settings['pipelines'] and \
                            int(status_id) == int(settings['pipelines']['status_for_new']):
                            
                            config['status_for_new'] = pipeline['name']+'/'+status['name']
                                
                        if 'status_for_rec' in settings['pipelines'] and \
                            int(status_id) == int(settings['pipelines']['status_for_rec']):
                                
                            config['status_for_rec'] = pipeline['name']+'/'+status['name']
                                
            if 'distribution_settings' in settings:
                for idx, distr_settings in enumerate(settings['distribution_settings']):
                    distr_user_name = next((user['name'] for user_id, user in user_cfg.cache \
                        ['_embedded']['users'].items() if user_id == distr_settings['user']), None)
                    settings['distribution_settings'][idx]['user'] = distr_user_name
                    
            config['weekdays'] = weekdays
            config['form_type'] = form_type
            config['public_hash'] = user_cfg.public_hash
            config['private_hash'] = user_cfg.private_hash
        
        log_info('Response', user_cfg.user.username, get_current_function(), config)
        return HttpResponse(json.dumps(config, sort_keys=True, ensure_ascii=False))
        
    except AmoException as e:
        context = e.context
        log_exception('', request.user.username, get_current_function(), context)
        return HttpResponseBadRequest()
    
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('configurator')

    return render(request, 'requestsHandler/login.html')
    
def log_user_out(request):
    logout(request)
    return redirect('login')

@login_required
@log_request(Message_type.INBOUND)
def newForm(request):
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest('Waiting for POST request')
        
        got_data = json.loads(request.body.decode('utf-8'))
        
        if not 'name' in got_data:
            return HttpResponseBadRequest('name is needed')
        if not 'type' in got_data or not got_data['type'] in config_types:
            return HttpResponseBadRequest('bad type')
            
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        name = got_data['name']
        form_type = got_data['type']
        
        if name and not name in get_config_forms(config):
            config[form_type][name] = {}
            if config_types[form_type]:
                config[form_type][name]['allowed_enum'] = config_types[form_type]
        else:
            return HttpResponseBadRequest()
            
        user_cfg.save()
        
        log_info('New form ', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
    
    except AmoException as e:
        context = e.context
        log_exception('', request.user.username, get_current_function(), context)
        return HttpResponseBadRequest()
    
@login_required
@log_request(Message_type.INBOUND)
def deleteForm(request):
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest('Waiting for POST request')
    
        got_data = json.loads(request.body.decode('utf-8'))
        if not 'name' in got_data:
            return HttpResponseBadRequest('name is needed')
        if not 'type' in got_data or not got_data['type'] in config_types:
            return HttpResponseBadRequest('bad type')
            
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        name = got_data['name']
        form_type = got_data['type']
        
        if name and name in config[form_type]:
            config[form_type].pop(name, None)
            luser = user_cfg.last_user_cache
            if form_type in luser and name in luser[form_type]:
                luser[form_type].pop(name, None)
            
        user_cfg.save()
        
        log_info('Deleted form ', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
    
    except AmoException as e:
        context = e.context
        log_exception('', request.user.username, get_current_function(), context)
        return HttpResponseBadRequest()
    
# @login_required
# @log_request(Message_type.INBOUND)
def test(request):
    # user_cfg = get_object_or_404(UserConfig, user=request.user)
    # api = AmoIntegr(user_cfg)

    return HttpResponse(200)
    