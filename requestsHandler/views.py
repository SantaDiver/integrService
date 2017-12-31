import json
import logging
import sys
from pprint import pprint
import time

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
import logging

from dadata.plugins.django import DjangoDaDataClient
from raven.contrib.django.raven_compat.models import client

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields, find_pipline_id
from utils import one_by_one, zero_department, not_chosen, ening_statuses, weekdays
from utils import get_config_forms
from requests_logger import log_request, log_exception, log_info, Message_type, \
    get_current_function
    
# TODO: Dadata city, email check (get it outside the form)
# TODO: test
# TODO: Private hash forms
# TODO: add admin pannel in user interface

logger = logging.getLogger(__name__)

@csrf_exempt
def siteHandler(request):
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest('Waiting for POST request')
        if not 'public_hash' in request.POST:
            return HttpResponseBadRequest('Public hash field is required')
        if not 'form' in request.POST:
            return HttpResponseBadRequest('Form field is required')
        
        user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
        log_info('Got data ', user_cfg.user.username, get_current_function(), request.POST)
        
        if not user_cfg.user.is_active:
            log_info('User is not active ', user_cfg.user.username, \
                get_current_function(), user_cfg.account_rights)
            raise Http404('User is not active!')
        
        if not request.POST['form'] in user_cfg.config:
            return HttpResponseNotFound('No form %s in config %s' % \
                (request.POST['form'], user_cfg.user.username))
        
        requested_form = request.POST['form']  
        api = AmoIntegr(user_cfg)
        
        data_to_send, generate_tasks_for_rec, department_id, internal_kwargs = conform_fields(
            request.POST, user_cfg.config[requested_form], user_cfg.account_rights)
                
        if 'distribution_settings' in user_cfg.config[requested_form] and \
            user_cfg.config[requested_form]['distribution_settings']:
            internal_kwargs['distribution_settings'] = \
               user_cfg.config[requested_form]['distribution_settings']
               
        if 'another_distribution' in user_cfg.config[request.POST['form']]:
            another_distribution = user_cfg.config[requested_form]['another_distribution']
            if another_distribution != not_chosen and another_distribution != requested_form:
                another_conform = user_cfg.config['another_distribution']
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
                requested_form = another_conform
        
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
        
        return HttpResponse('OK')
        
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
        return HttpResponseBadRequest()

@login_required
@log_request(Message_type.INBOUND)
def configurator(request):
    try:
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        config_names = get_config_forms(config)
        
        if not request.path[1:] or request.path[1:] in config or \
            request.path[1:] in ['add_form', 'accesses']:
            return render(request, 'requestsHandler/configurator.html', {
                'config_names':config_names, 
                'username': user_cfg.user.username
            })
        else:
            raise Http404('Path %s wasnt found' % request.path[1:])
            
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
        return HttpResponseBadRequest()
    

@login_required
@log_request(Message_type.INBOUND)
def setConfig(request):
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest('Waiting for POST request')
            
        got_config = json.loads(request.body.decode('utf-8'))
        if not 'form' in got_config:
            return HttpResponseNotFound('Form field is required')
        
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        log_info('Config before updateing', user_cfg.user.username, get_current_function(), user_cfg.config)
        
        first_lvl_data = ['user', 'subdomain', 'hash']
        for field in first_lvl_data:
            if field in got_config:
                if field == 'time_to_complete_rec_task':
                    got_config[field] *= 60
                user_cfg.config[field] = got_config[field]
                
        if got_config['form'] == 'accesses':
            user_cfg.save()
            return HttpResponse(200)
        
        if not got_config['form'] in user_cfg.config:
            return HttpResponseNotFound('No form %s in config %s' % \
                (got_config['form'], user_cfg.user.username))
                
        form = got_config['form']
        
        if not 'fields_to_check_dups' in user_cfg.config[form]:
            user_cfg.config[form]['fields_to_check_dups'] = {}
        if 'contact_fields_to_check_dups' in got_config:
            user_cfg.config[form]['fields_to_check_dups']['contacts'] = \
                [field['field'] for field in got_config['contact_fields_to_check_dups']]
        if 'company_fields_to_check_dups' in got_config:
            user_cfg.config[form]['fields_to_check_dups']['companies'] = \
                [field['field'] for field in got_config['company_fields_to_check_dups']]
        
        additional_params = ['rec_lead_task_text', 'time_to_complete_rec_task', 'another_distribution']
        for param in additional_params:
            if param in got_config:
                if param == 'time_to_complete_rec_task':
                    got_config[param] *= 60
                user_cfg.config[form][param] =  got_config[param]
                
        if 'generate_tasks_for_rec' in got_config:
            user_cfg.config[form]['generate_tasks_for_rec'] = \
                got_config['generate_tasks_for_rec']
        if 'tag_for_rec' in got_config:
             user_cfg.config[form]['tag_for_rec'] = \
                got_config['tag_for_rec']
                
        if '_embedded' in user_cfg.cache:
            if 'distribution_settings' in got_config:
                for idx, distr_settings in enumerate(got_config['distribution_settings']):
                    distr_user_id = next((user_id for user_id, user in user_cfg.cache \
                        ['_embedded']['users'].items() if user['name'] == distr_settings['user']), None)
                    got_config['distribution_settings'][idx]['user'] = distr_user_id
                
                if not 'distribution_settings' in user_cfg.config[form]:
                     user_cfg.config[form]['distribution_settings'] = \
                        got_config['distribution_settings']
                else:
                    pairs = zip(user_cfg.config[form]['distribution_settings'], \
                        got_config['distribution_settings'])
                    if any(x != y for x, y in pairs):
                        user_cfg.last_user_cache[form] = {}
                    user_cfg.config[form]['distribution_settings'] = got_config['distribution_settings']
            
            if 'responsible_user' in got_config:
                if got_config['responsible_user'] == one_by_one:
                    user_cfg.config[form]['responsible_user_id'] = one_by_one
                else:
                    for user_id, user in user_cfg.cache['_embedded']['users'].items():
                        if user['name'] == got_config['responsible_user']:
                             user_cfg.config[form]['responsible_user_id'] = user_id
                             
            if 'department' in got_config:
                if got_config['department'] == zero_department:
                    user_cfg.config[form]['department_id'] = 0
                elif got_config['department'] == not_chosen:
                    user_cfg.config[form]['department_id'] = not_chosen
                else:
                    for group_id, group in user_cfg.cache['_embedded']['groups'].items():
                        if group['name'] == got_config['department']:
                             user_cfg.config[form]['department_id'] = group_id
            
            if not 'pipelines' in user_cfg.config[form]:
                user_cfg.config[form]['pipelines'] = {}
            if 'status_for_new' in got_config:
                user_cfg.config[form]['pipelines']['status_for_new'] = \
                    find_pipline_id(user_cfg.cache['_embedded']['pipelines'], got_config['status_for_new'])
            if 'status_for_rec' in got_config:
                user_cfg.config[form]['pipelines']['status_for_rec'] = \
                    find_pipline_id(user_cfg.cache['_embedded']['pipelines'], got_config['status_for_rec'])
                    
            if 'contact_fields' in got_config:
                user_cfg.config[form]['contact_data'] = {}
                for field in got_config['contact_fields']:
                    user_cfg.config[form]['contact_data'][field['amoCRM']] = field['site']
                    
            if 'company_fields' in got_config:
                user_cfg.config[form]['company_data'] = {}
                for field in got_config['company_fields']:
                    user_cfg.config[form]['company_data'][field['amoCRM']] = field['site']
                    
            if 'lead_fields' in got_config:
                user_cfg.config[form]['lead_data'] = {}
                for field in got_config['lead_fields']:
                    user_cfg.config[form]['lead_data'][field['amoCRM']] = field['site']
                
            
        user_cfg.save()
        
        log_info('Updated config', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
        
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
        return HttpResponseBadRequest()
    
@login_required 
@log_request(Message_type.INBOUND)
def getConfig(request):
    try:
        if request.method != 'GET':
            return HttpResponseBadRequest('Waiting for GET request')
        if not 'hash' in request.GET:
            return HttpResponseBadRequest('Hash parameter needed!')
            
        requested_form = request.GET['hash']
        
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        config = user_cfg.config
        
        if not requested_form in config and requested_form != 'accesses':
            log_info('Response', user_cfg.user.username, get_current_function(), config)
            return HttpResponseNotFound('No form %s in config %s' % \
                (requested_form, user_cfg.user.username))
        
        config['forms'] = get_config_forms(config)
        config['forms'].append(not_chosen)
        
        config['valid_amo'] = True
        
        try:
            api = AmoIntegr(user_cfg)
            api.force_to_update_cache()
        except AmoException as e:
            config['valid_amo'] = False
        
        def RepresentsInt(s):
            try: 
                int(s)
                return True
            except ValueError:
                return False
            
        config['allowed_fields'] = {}
        config['allowed_statuses'] = []
        if '_embedded' in user_cfg.cache and requested_form in config:
            if not 'fields_to_check_dups' in config[requested_form]:
                config[requested_form]['fields_to_check_dups'] = {}
            
            contact_field_options = [field for field in user_cfg.fields_cache['contacts'] if not RepresentsInt(field)]
            contact_field_options += ['name', 'default_name', 'tags']
            
            company_field_options = [field for field in user_cfg.fields_cache['companies'] if not RepresentsInt(field)]
            company_field_options += ['name', 'default_name', 'tags']
            
            lead_field_options = [field for field in user_cfg.fields_cache['leads'] if not RepresentsInt(field)]
            lead_field_options += ['name', 'default_name', 'tags']
            
            config = user_cfg.config
            config['allowed_fields'] = {
                'contacts' : contact_field_options,
                'companies' : company_field_options,
                'leads' : lead_field_options
            }
            
            config['allowed_users'] = [user['name'] for user_id, user in 
                user_cfg.cache['_embedded']['users'].items() if not user['is_free'] and user['is_active']]
            config['allowed_users'].append(one_by_one)
            
            for pipeline_id, pipeline in user_cfg.cache['_embedded']['pipelines'].items():
                for status_id, status in pipeline['statuses'].items():
                    config['allowed_statuses'].append(pipeline['name']+'/'+status['name'])
            
            if 'responsible_user_id' in config[requested_form] and \
                config[requested_form]['responsible_user_id'] != one_by_one:
                config['default_user'] = [user['name'] for user_id, user in 
                    user_cfg.cache['_embedded']['users'].items() if 
                    int(user_id) == int(config[requested_form]['responsible_user_id'])][0]
            else:
                config['default_user'] = one_by_one
                
            config['allowed_departments'] = [group['name'] for group_id, group in 
                user_cfg.cache['_embedded']['groups'].items()]
            config['allowed_departments'].append(zero_department)
            config['allowed_departments'].append(not_chosen)
            
            config['default_department'] = not_chosen
            if 'department_id' in config[requested_form]:
                if config[requested_form]['department_id'] != 0 and \
                    config[requested_form]['department_id'] != not_chosen:
                    config['default_department'] = [group['name'] for group_id, group in 
                    user_cfg.cache['_embedded']['groups'].items() if 
                        int(group_id) == int(config[requested_form]['department_id'])][0]
                elif config[requested_form]['department_id'] == 0:
                    config['default_department'] = zero_department
                
            if 'pipelines' in config[requested_form]:
                for pipeline_id, pipeline in user_cfg.cache['_embedded']['pipelines'].items():
                    for status_id, status in pipeline['statuses'].items():
                        if 'status_for_new' in config[requested_form]['pipelines'] and \
                            int(status_id) == int(config[requested_form]['pipelines']['status_for_new']):
                            
                            if not int(status_id) in ening_statuses:
                                config['status_for_new'] = pipeline['name']+'/'+status['name']
                            else:
                                config['status_for_new'] = status['name']
                                
                        if 'status_for_rec' in config[requested_form]['pipelines'] and \
                            int(status_id) == int(config[requested_form]['pipelines']['status_for_rec']):
                                
                            if not int(status_id) in ening_statuses:
                                config['status_for_rec'] = pipeline['name']+'/'+status['name']
                            else:
                                config['status_for_rec'] = status['name']
                                
            if 'distribution_settings' in config[requested_form]:
                for idx, distr_settings in enumerate(config[requested_form]['distribution_settings']):
                    distr_user_name = next((user['name'] for user_id, user in user_cfg.cache \
                        ['_embedded']['users'].items() if user_id == distr_settings['user']), None)
                    config[requested_form]['distribution_settings'][idx]['user'] = distr_user_name
                    
            config['weekdays'] = weekdays
        
        log_info('Response', user_cfg.user.username, get_current_function(), config)
        return HttpResponse(json.dumps(config, sort_keys=True, ensure_ascii=False))
        
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
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
            
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        
        if got_data['name'] and not got_data['name'] in user_cfg.config:
            user_cfg.config[got_data['name']] = {}
        else:
            return HttpResponseBadRequest()
            
        user_cfg.save()
        
        log_info('New form ', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
    
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
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
            
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        
        if got_data['name'] and got_data['name'] in user_cfg.config:
            user_cfg.config.pop(got_data['name'], None)
            user_cfg.last_user_cache.pop(got_data['name'], None)
            
        user_cfg.save()
        
        log_info('Deleted form ', user_cfg.user.username, get_current_function(), user_cfg.config)
        return HttpResponse(200)
    
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
        return HttpResponseBadRequest()
    
@login_required
@log_request(Message_type.INBOUND)
def test(request):
    try:
        user_cfg = get_object_or_404(UserConfig, user=request.user)
        api = AmoIntegr(user_cfg)
        api.add_entity('here', 'wow',2, {})
    
    except AmoException as e:
        context = e.context
        log_exception(request.user.username, context)
    
    # api.add_entity('there', 'wow',2, {})
    return HttpResponse(200)
    