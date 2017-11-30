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
            "Поле 5" : 911,
            "Должность" : "Some",
            "Телефон" : {"WORK" : "0000"},
            "Тип" : ["вар1"],
            "Email" : {"WORK" : "email-mail"}
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
    
    additional_data_to_query = {
        "contacts" : {
            "Телефон" : {"WORK" : "123123"}
        }
    }
    
    # pprint(api.get_links("contacts", 27405655))
    # pprint(api.get_customers(id=54943))
        
    api.send_order_data(contact_data = contact_data, lead_data=lead_data, 
        responsible_user_id=845532)
    
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