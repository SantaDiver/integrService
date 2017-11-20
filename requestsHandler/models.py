from django.db import models
from django.contrib.postgres.fields import JSONField

import hashlib
import time

def _createHash():
    """This function generate 10 character long hash"""
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return  hash.hexdigest()

# Create your models here.

class UserConfig(models.Model):
    user_hash = models.CharField(max_length=40, default=_createHash(),unique=True)
    config = JSONField(default={'foo': 'bar'})