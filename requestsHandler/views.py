import json
import logging
import sys

from pprint import pprint

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from requestsHandler.models import UserConfig

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
        "Поле 5" : 911,
        "Должность" : "Some",
        "Телефон" : {"WORK" : "2148354", "MOB" : "098"},
        "Тип" : ["вар1"],
        "Email" : {"WORK" : "email-mail"}
    }
        
    lead_data = {
        "что-то" : 1000000
    }
    
    # api.add_entity("leads", "Test123098", 1408894, lead_data, price=1011)
    # pprint(user_cfg.fields_cache)
    # dups = api.find_duplicates(contact_data, "contacts", ["Телефон"])
    
    api.send_order_data(contact_data = contact_data)
    
    user_cfg.save()
        
    return HttpResponse("OK")