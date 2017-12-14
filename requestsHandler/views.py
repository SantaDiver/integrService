import json
import logging
import sys

from pprint import pprint

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
        return HttpResponse("It should be post")
    if not 'public_hash' in request.POST:
        return HttpResponse("Public hash should exist")
    
    user_cfg = get_object_or_404(UserConfig, public_hash=request.POST['public_hash'])
    
    api = AmoIntegr(user_cfg)
    
    contact_data = {
        "name" : "Тест",
        "custom_fields" : {
            "Должность" : "Some",
            "Телефон" : {"WORK" : "0000"},
            "Тип" : ["вар6"],
            "Email" : [{"WORK" : "email-mail"}, {"WORK" : "email-2mail"}],
            # "Адрес" : {"city" : "Хуерод", "country" : "RU"}
        },
        "tags" : "Тег3"
    }
        
    lead_data = {
        "name" : "Тестик",
        "custom_fields" : {
            "что-то" : 1000000
        },
        "tags" : "Тег3, Тег4"
    }
    
    company_data = {
        "name" : "Тест",
        "custom_fields" : {
            "Телефон" : {"WORK" : "0000"},
            "Где ведут учет" : "CRM"
        },
        "tags" : "Тег3"
    }
    
    additional_data_to_query = {
        "contacts" : {
            "Тип" : ["Вар4", "Вар3"]
        }
    }
    
    pprint(api.get_entity("contacts"))
        
    # api.send_order_data(contact_data = contact_data, lead_data=lead_data, department_id=53910,
    #     additional_data_to_query=additional_data_to_query)
    
    # client = DjangoDaDataClient()
    
    # client.phone = "+7(9 26)214 83-5 4"
    # client.phone.request()
    # pprint(client.result.phone)
    # pprint(client.result.number)
    # pprint(client.result.provider)
    # pprint(client.result.region)
    # pprint(client.result.timezone)
    
    user_cfg.save()
        
    return HttpResponse("OK")