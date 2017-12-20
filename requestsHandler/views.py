import json
import logging
import sys
from pprint import pprint
import time

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from requestsHandler.models import UserConfig

from dadata.plugins.django import DjangoDaDataClient

sys.path.insert(0, './amoIntegr')
sys.path.insert(0, './requestsHandler')
from amoIntegr import AmoIntegr
from amoException import AmoException
from conform_fields import conform_fields
    
# TODO: Dadata city check
# TODO: delete whitespace from tags
@csrf_exempt
def siteHandler(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
    if not 'public_hash' in request.POST:
        return HttpResponse("Public hash field is required")
    
    user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
    
    if not "site_fields_conformity" in user_cfg.config:
        raise Exception("No site_fields_conformity in config %s" % user_cfg.user.username)
    
    api = AmoIntegr(user_cfg)
    
    data_to_send, generate_tasks_for_rec, department_id, internal_kwargs = conform_fields(
        request.POST, user_cfg.config["site_fields_conformity"])
            
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

@csrf_exempt   
def cacheUpdate(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
    if not 'public_hash' in request.POST:
        return HttpResponse("Public hash field is required")
    
    user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
    
    api = AmoIntegr(user_cfg)
    
    api.update_cache()
              
    user_cfg.save()
        
    return HttpResponse("Cache for user %s updated!" % user_cfg.user.username)
    
def configurator(request):
    user_cfg = get_object_or_404(UserConfig, public_hash=1)
    api = AmoIntegr(user_cfg)
    api.update_cache()
    
    def RepresentsInt(s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
    contact_field_options = [field for field in user_cfg.fields_cache["contacts"] if not RepresentsInt(field)]
    contact_field_options += ["default_name", "name", "tags"]
    
    config = user_cfg.config
    config["allowed_fields"] = {
        "contacts" : contact_field_options,
    }
    
    
    return render(request, 'requestsHandler/configurator.html', config)