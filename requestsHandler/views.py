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
from django.http import HttpResponseNotFound
from django.http import Http404
from requestsHandler.models import UserConfig

from dadata.plugins.django import DjangoDaDataClient

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields, find_pipline_id
from utils import one_by_one, zero_department, not_chosen, ening_statuses
    
# TODO: Dadata city check
# TODO: delete whitespace from tags
# TODO: put everiything inside site_form_conformity
@csrf_exempt
def siteHandler(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
    if not 'public_hash' in request.POST:
        return HttpResponse("Public hash field is required")
    if not 'form' in request.POST:
        return HttpResponse("Public hash field is required")
    
    user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
    
    if not request.POST['form'] in user_cfg.config:
        return HttpResponseNotFound("No form %s in config %s" % \
            (request.POST['form'], user_cfg.user.username))
    
    api = AmoIntegr(user_cfg)
    
    data_to_send, generate_tasks_for_rec, department_id, internal_kwargs = conform_fields(
        request.POST, user_cfg.config[request.POST['form']])
            
    reslut = api.send_order_data(
        contact_data = data_to_send["contact_data"], 
        lead_data=data_to_send["lead_data"], 
        company_data=data_to_send["company_data"], 
        department_id=department_id, 
        generate_tasks_for_rec = generate_tasks_for_rec,
        **internal_kwargs
    )    
              
    user_cfg.save()
        
    return HttpResponse("OK")

@login_required
def configurator(request):
    user_cfg = get_object_or_404(UserConfig, user=request.user)
    config = user_cfg.config
    
    config_names = []
    for key in config:
        if not key in ['cache_ttl', 'subdomain', 'hash', 'user']:
            config_names.append(key)
    
    if not request.path[1:] or request.path[1:] in config or \
        request.path[1:] in ['add_form', 'accesses']:
        return render(request, 'requestsHandler/configurator.html', {'config_names':config_names})
    else:
        raise Http404('Path %s wasnt found' % request.path[1:])
    

@login_required
def setConfig(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
        
    got_config = json.loads(request.body.decode("utf-8"))
    if not 'form' in got_config:
        return HttpResponseNotFound("Form field is required")
    
    user_cfg = get_object_or_404(UserConfig, user=request.user)
    
    first_lvl_data = ["user", "subdomain", "hash"]
    for field in first_lvl_data:
        if field in got_config:
            if field == "time_to_complete_rec_task":
                got_config[field] *= 60
            user_cfg.config[field] = got_config[field]
            
    if got_config['form'] == 'accesses':
        pprint(got_config)
        user_cfg.save()
        return HttpResponse(200)
    
    if not got_config['form'] in user_cfg.config:
        return HttpResponseNotFound("No form %s in config %s" % \
            (got_config['form'], user_cfg.user.username))
            
    form = got_config['form']
    
    if not "fields_to_check_dups" in user_cfg.config[form]:
        user_cfg.config[form]["fields_to_check_dups"] = {}
    if "contact_fields_to_check_dups" in got_config:
        user_cfg.config[form]["fields_to_check_dups"]["contacts"] = \
            [field["field"] for field in got_config["contact_fields_to_check_dups"]]
    if "company_fields_to_check_dups" in got_config:
        user_cfg.config[form]["fields_to_check_dups"]["companies"] = \
            [field["field"] for field in got_config["company_fields_to_check_dups"]]
    
    additional_params = ['rec_lead_task_text', 'time_to_complete_rec_task']
    for param in additional_params:
        if param in got_config:
            if param == 'time_to_complete_rec_task':
                got_config[param] *= 60
            user_cfg.config[form][param] =  got_config[param]
            
    if "generate_tasks_for_rec" in got_config:
        user_cfg.config[form]["generate_tasks_for_rec"] = \
            got_config["generate_tasks_for_rec"]
    if "tag_for_rec" in got_config:
         user_cfg.config[form]["tag_for_rec"] = \
            got_config["tag_for_rec"]
            
    if "_embedded" in user_cfg.cache:
        if "responsible_user" in got_config:
            if got_config["responsible_user"] == one_by_one:
                user_cfg.config[form]["responsible_user_id"] = one_by_one
            else:
                for user_id, user in user_cfg.cache["_embedded"]["users"].items():
                    if user["name"] == got_config["responsible_user"]:
                         user_cfg.config[form]["responsible_user_id"] = user_id
                         
        if "department" in got_config:
            if got_config["department"] == zero_department:
                user_cfg.config[form]["department_id"] = 0
            elif got_config["department"] == not_chosen:
                user_cfg.config[form]["department_id"] = not_chosen
            else:
                for group_id, group in user_cfg.cache["_embedded"]["groups"].items():
                    if group["name"] == got_config["department"]:
                         user_cfg.config[form]["department_id"] = group_id
        
        if not "pipelines" in user_cfg.config[form]:
            user_cfg.config[form]["pipelines"] = {}
        if "status_for_new" in got_config:
            user_cfg.config[form]["pipelines"]["status_for_new"] = \
                find_pipline_id(user_cfg.cache["_embedded"]["pipelines"], got_config["status_for_new"])
        if "status_for_rec" in got_config:
            user_cfg.config[form]["pipelines"]["status_for_rec"] = \
                find_pipline_id(user_cfg.cache["_embedded"]["pipelines"], got_config["status_for_rec"])
                
        if "contact_fields" in got_config:
            user_cfg.config[form]["contact_data"] = {}
            for field in got_config["contact_fields"]:
                user_cfg.config[form]["contact_data"][field["amoCRM"]] = field["site"]
                
        if "company_fields" in got_config:
            user_cfg.config[form]["company_data"] = {}
            for field in got_config["company_fields"]:
                user_cfg.config[form]["company_data"][field["amoCRM"]] = field["site"]
                
        if "lead_fields" in got_config:
            user_cfg.config[form]["lead_data"] = {}
            for field in got_config["lead_fields"]:
                user_cfg.config[form]["lead_data"][field["amoCRM"]] = field["site"]
            
        
    user_cfg.save()
    return HttpResponse(200)
    
@login_required 
def getConfig(request):
    if request.method != 'GET':
        return HttpResponse("Waiting for GET request")
    if not "hash" in request.GET:
        return HttpResponse("Hash parameter needed!")
        
    requested_form = request.GET['hash']
            
    user_cfg = get_object_or_404(UserConfig, user=request.user)
    config = user_cfg.config
    if not requested_form in config and requested_form != "accesses":
        return HttpResponseNotFound("No form %s in config %s" % \
            (requested_form, user_cfg.user.username))
    
    config["valid_amo"] = True
    
    try:
        api = AmoIntegr(user_cfg)
        api.force_to_update_cache()
    except AmoException as e:
        config["valid_amo"] = False
    
    def RepresentsInt(s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
        
    config["allowed_fields"] = {}
    config["allowed_statuses"] = []
    if "_embedded" in user_cfg.cache and requested_form in config:
        if not 'fields_to_check_dups' in config[requested_form]:
            config[requested_form]['fields_to_check_dups'] = {}
        
        contact_field_options = [field for field in user_cfg.fields_cache["contacts"] if not RepresentsInt(field)]
        contact_field_options += ["default_name", "name", "tags"]
        
        company_field_options = [field for field in user_cfg.fields_cache["companies"] if not RepresentsInt(field)]
        company_field_options += ["default_name", "name", "tags"]
        
        lead_field_options = [field for field in user_cfg.fields_cache["leads"] if not RepresentsInt(field)]
        lead_field_options += ["default_name", "name", "tags"]
        
        config = user_cfg.config
        config["allowed_fields"] = {
            "contacts" : contact_field_options,
            "companies" : company_field_options,
            "leads" : lead_field_options
        }
        
        config["allowed_users"] = [user["name"] for user_id, user in 
            user_cfg.cache["_embedded"]["users"].items() if not user["is_free"]]
        config["allowed_users"].append(one_by_one)
        
        for pipeline_id, pipeline in user_cfg.cache["_embedded"]["pipelines"].items():
            for status_id, status in pipeline["statuses"].items():
                config["allowed_statuses"].append(pipeline["name"]+"/"+status["name"])
        
        if "responsible_user_id" in config[requested_form] and \
            config[requested_form]["responsible_user_id"] != one_by_one:
            config["default_user"] = [user["name"] for user_id, user in 
                user_cfg.cache["_embedded"]["users"].items() if 
                int(user_id) == int(config[requested_form]["responsible_user_id"])][0]
        else:
            config["default_user"] = one_by_one
            
        config["allowed_departments"] = [group["name"] for group_id, group in 
            user_cfg.cache["_embedded"]["groups"].items()]
        config["allowed_departments"].append(zero_department)
        config["allowed_departments"].append(not_chosen)
        
        config["default_department"] = not_chosen
        if "department_id" in config[requested_form]:
            if config[requested_form]["department_id"] != 0 and \
                config[requested_form]["department_id"] != not_chosen:
                config["default_department"] = [group["name"] for group_id, group in 
                user_cfg.cache["_embedded"]["groups"].items() if 
                    int(group_id) == int(config[requested_form]["department_id"])][0]
            elif config[requested_form]["department_id"] == 0:
                config["default_department"] = zero_department
            
        if "pipelines" in config[requested_form]:
            for pipeline_id, pipeline in user_cfg.cache["_embedded"]["pipelines"].items():
                for status_id, status in pipeline["statuses"].items():
                    if "status_for_new" in config[requested_form]["pipelines"] and \
                        int(status_id) == int(config[requested_form]["pipelines"]["status_for_new"]):
                        
                        if not int(status_id) in ening_statuses:
                            config["status_for_new"] = pipeline["name"]+"/"+status["name"]
                        else:
                            config["status_for_new"] = status["name"]
                            
                    if "status_for_rec" in config[requested_form]["pipelines"] and \
                        int(status_id) == int(config[requested_form]["pipelines"]["status_for_rec"]):
                            
                        if not int(status_id) in ening_statuses:
                            config["status_for_rec"] = pipeline["name"]+"/"+status["name"]
                        else:
                            config["status_for_rec"] = status["name"]  
    
    return HttpResponse(json.dumps(config, sort_keys=True, ensure_ascii=False))
    
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
def newForm(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
    if not 'name' in request.POST:
        return HttpResponse("name is needed")
        
    user_cfg = get_object_or_404(UserConfig, user=request.user)
    
    if request.POST['name'] and not request.POST['name'] in user_cfg.config:
        user_cfg.config[request.POST['name']] = {}
        
    user_cfg.save()
    
    return redirect('configurator')


    