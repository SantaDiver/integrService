from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from pprint import pprint;
# Create your views here.

@csrf_exempt
def basicHandler(request):
    if request.method == 'POST':
        pprint(request.POST)
        return HttpResponse("Yep")
    elif request.method == 'GET':
        return HttpResponse("It's get")