from django.contrib import admin
from .models import UserConfig

import json

from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget

# Register your models here.

from jsoneditor.forms import JSONEditor
@admin.register(UserConfig)
class MyAdmin(admin.ModelAdmin):
    list_display = ("get_username", "get_email")
    raw_id_fields = ("user",)
    search_fields = ("user__username",)
    
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
        # Using Pretty json
        # JSONField: {'widget': PrettyJSONWidget }
    }
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = "Username"
        
    def get_email(self, obj):
        return "<a href='mailto:%s'>%s</a>" % (obj.user.email, obj.user.email,)
    get_email.allow_tags = True
    get_email.short_description = "Email"

    