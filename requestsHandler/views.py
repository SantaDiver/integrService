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

sys.path.insert(0, '/home/ubuntu/workspace/amoIntegr')
from amoIntegr import AmoIntegr
from amoException import AmoException

# Create your views here.
    
@csrf_exempt
def basicHandler(request):
    if request.method != 'POST':
        return HttpResponse("Waiting for POST request")
    if not 'public_hash' in request.POST:
        return HttpResponse("Public hash field is required")
    
    user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
    
    if not "site-fields-conformity" in user_cfg.config:
        raise Exception("No site-fields-conformity in config %s" % user_cfg.user.username)
    
    api = AmoIntegr(user_cfg)
    
    data_to_send = {
        "contact_data" : {},
        "company_data" : {},
        "lead_data" : {}
    }
    
    for data_type in ["contact_data", "company_data", "lead_data"]:
        if data_type in user_cfg.config["site-fields-conformity"]:
            conformity = user_cfg.config["site-fields-conformity"]["contact_data"]
            
            if "name" in conformity and conformity["name"] in request.POST:
                data_to_send[data_type]["name"] = request.POST[conformity["name"]]
            elif "default-name" in conformity:
                data_to_send[data_type]["name"] = conformity["default-name"]
            elif data_type == "lead_data":
                data_to_send[data_type]["name"] = None
            else:
                raise Exception("No name for contact")
                
            data_to_send[data_type]["custom_fields"] = {}
            for field, field_alias in conformity.items():
                if not field in ["name", "default-name"] and field_alias in request.POST:
                    if not field in ["Телефон", "Email"]:
                        data_to_send[data_type]["custom_fields"][field] = request.POST[field_alias]
                    else:
                        data_to_send[data_type]["custom_fields"][field] = {
                            "WORK" : request.POST[field_alias]
                        }
                        
            if "tags" in conformity:
                data_to_send[data_type]["tags"] = conformity["tags"]
    
    conf = user_cfg.config["site-fields-conformity"]
    
    generate_tasks_for_rec = False
    if "generate_tasks_for_rec" in conf:
        generate_tasks_for_rec = conf["generate_tasks_for_rec"]
    
    department_id = -1
    if "department_id" in conf:
        department_id = conf["department_id"]
        
    
    internal_kwargs = {"additional_data_to_query" : {}}
    if "pipelines" in conf:
        internal_kwargs["pipelines"] = conf["pipelines"]
    if "responsible_user_id" in conf:
        internal_kwargs["responsible_user_id"] = conf["responsible_user_id"]
    if "tag_for_rec" in conf:
        internal_kwargs["tag_for_rec"] = conf["tag_for_rec"]
        
    if "dadata-phone-check" in conf and conf["dadata-phone-check"]:
        client = DjangoDaDataClient()
        internal_kwargs["additional_data_to_query"]["Телефон"] = []
        
        for data_type in ["contact_data", "company_data"]:
            if "custom_fields" in data_to_send[data_type] and "Телефон" in \
                data_to_send[data_type]["custom_fields"]:
                
                for key,value in data_to_send[data_type]["custom_fields"]["Телефон"].items():
                    client.phone = value
                    client.phone.request()
                    
                    print(data_type)
                    if client.result.phone != None:
                        data_to_send[data_type]["custom_fields"]["Телефон"][key] = client.result.phone
                    
                    if client.result.number != None:
                        internal_kwargs["additional_data_to_query"]["Телефон"].append({
                            "WORK" : client.result.number
                        })
            
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