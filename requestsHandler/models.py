from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

import hashlib
import time

import json

def _createHash():
    """This function generate 10 character long hash"""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return  hash.hexdigest()
    
def get_default_user():
    return User.objects.get(id=1)
    
def get_default_config():
    return {
        'cache_ttl' : 300,
        'user' : 'user',
        'subdomain' : 'subdomain',
        'hash' : 'hash',
        'site_forms' : {},
        'jivo_site' : {},
        'email' : {},
        'onpbx' : {},
    }

def get_default_rights():
    return {
        'paid_till' : time.time()
    }

# Create your models here.
class UserConfig(models.Model):
    public_hash = models.CharField(max_length=40, default=_createHash(), 
        unique=True, db_index=True)
    private_hash = models.CharField(max_length=40, default=_createHash(), 
        unique=True, db_index=True)
    
    user = models.OneToOneField(User, default=get_default_user)
    
    config = JSONField(default=get_default_config(), blank=True)
    account_rights = JSONField(default=get_default_rights(), blank=True)
    cache = JSONField(default={}, blank=True)
    fields_cache = JSONField(default={}, blank=True)
    last_user_cache = JSONField(default={}, blank=True)
    
    
    history = HistoricalRecords()