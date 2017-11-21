# TODO: add functiond for getting/adding/updateing with useful names

import json
import requests
import time
from pprint import pprint
import os.path
import sys

from utils import get_method_by_request
from utils import entity_optional_params

from amoException import AmoException

class AmoIntegr(object):
    def __init__(self, user):
        self.user = user
        self.cfg = user.config
        self.request = requests.session()
        self._auth()
            
    def _auth(self):
        url = "https://%s.amocrm.ru/private/api/auth.php?type=json" % (
            self.cfg["subdomain"])

        response = self.request.post(url, json = {
            "USER_LOGIN" : self.cfg["user"],
            "USER_HASH" : self.cfg["hash"],
            "type" : "json"
        })

        if not response.json()["response"]["auth"]:
            raise AmoException("Auth Failed", response)
            
            
    def call(self, request, params = []):
        url = "https://%s.amocrm.ru/private/api/v2/json/%s" % (
                self.cfg["subdomain"], request)

        if get_method_by_request(request) == "GET":
            response = self.request.get(url, params = params)
        else:
            response = self.request.post(url, json = params)
            
        if (response.status_code == 401):
            self._auth()
            if get_method_by_request(request) == "GET":
                response = self.request.get(url, params = params)
            else:
                response = self.request.post(url, json = params)

        if (response.status_code != 200):
            message = "Status code is %s" % response.status_code
            raise AmoException(message, response)

        return response.json()["response"]
        
    def cache_special_type_fields(self, type_of_element, cache):
        result_cache = {}
        for field in cache["account"]["custom_fields"][type_of_element]:
            if field["code"]:
                result_cache[field["code"]] = field
            result_cache[field["name"]] = field
            result_cache[field["id"]] = field
            
        return result_cache
            
    def cache_fields(self):
        cache = self.user.cache
        fields_cache = {}
        type_of_elements = ["contacts", "leads"]
        for type_of_element in type_of_elements:
            fields_cache[type_of_element] = self.cache_special_type_fields(type_of_element, cache)
        
        self.user.fields_cache = fields_cache
    
    def force_to_update_cache(self):
        resp = self.call('accounts/current')
        resp["timestamp"] = time.time()
        self.user.cache = resp
                
    def update_cache(self):
        cache = self.user.cache
        if not "timestamp" in cache:
            self.force_to_update_cache()
            self.cache_fields()
        elif time.time() - cache["timestamp"] > int(self.cfg["cache-ttl"]):
            self.force_to_update_cache()
            self.cache_fields()
            
    def translate_fields(self, fields, type_of_element):
        self.update_cache()
        fields_cache = self.user.fields_cache
        translated_fields = []
        for (name, value) in fields.items():
            if not value:
                raise AmoException("Empty field value!", None)
            
            field_from_cache = fields_cache[type_of_element][name]
           
            translated_field = {
                "id" : field_from_cache["id"],
                "values" : []
            }

            if field_from_cache["multiple"] == "Y":
                
                for (enum, subvalue) in value.items():
                    enum_dict = dict((v,k) 
                        for (k,v) in field_from_cache["enums"].items())
                    translated_field["values"].append({
                        "value" : subvalue,
                        "enum" : enum_dict[enum]
                    })
            
            else:
                if type(value) is list:
                    enum_dict = dict((v,k) 
                        for (k,v) in field_from_cache["enums"].items())
                    for subvalue in value:
                        translated_field["values"].append({
                            "enum" : enum_dict[subvalue],
                            "value" : subvalue
                        })
                else:
                    translated_field["values"].append({
                        "value" : value,
                    })

            translated_fields.append(translated_field)
        
        return translated_fields
    
    # Works with contacts, leads, companies, customers. Doesn't work with tasks!
    def add_entity(self, entity_type, name, responsible_user_id, custom_fields, 
        **kwargs):
            
        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        self.update_cache()    
        cache = self.user.cache
        if entity_type == "customers" and cache["account"]["customers_enabled"] != "Y":
                raise AmoException("Customers are not enabled!", None)
        
        translated_fields = self.translate_fields(custom_fields, entity_type)
        if entity_type != "customers":
            params_to_pass = {
                "name" : name,
                "responsible_user_id" : responsible_user_id,
                "custom_fields" : translated_fields,
                "created_user_id" : 0,
            }
        else:
            params_to_pass = {
                "name" : name,
                "main_user_id" : responsible_user_id,
                "custom_fields" : translated_fields,
                "created_by" : 0,
            }
        
        for (key, value) in kwargs.items():
            if key in entity_optional_params[entity_type]:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        json_to_pass = {
            "request" : {
                entity_type : {
                    "add" : [params_to_pass]
                }
            }
        }
        
        if entity_type == "companies":
            entity_type = "company"
        # print(json.dumps(json_to_pass, ensure_ascii=False))
        return self.call("%s/set" % entity_type, json_to_pass)
    
    # Works with contacts, leads, companies, customers. Doesn't work with tasks!
    def update_entity(self, entity_type, entity_id, last_modified, **kwargs):
            
        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
            
        self.update_cache()    
        cache = self.user.cache
        
        if entity_type == "customers" and cache["account"]["customers_enabled"] != "Y":
                raise AmoException("Customers are not enabled!", None)
        
        params_to_pass = {
            "id" : entity_id,
            "last_modified" : last_modified
        }
        
        if "custom_fields" in kwargs:
            params_to_pass["custom_fields"] = self.translate_fields(
                kwargs["custom_fields"], entity_type)
                
        if entity_type != "customers":
            mutual_params = ["name", "responsible_user_id", "created_user_id"]
        else:
            mutual_params = ["name", "main_user_id", "created_by"]
        
        for (key, value) in kwargs.items():
            if key in entity_optional_params[entity_type] or key in mutual_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        json_to_pass = {
            "request" : {
                entity_type : {
                    "update" : [params_to_pass]
                }
            }
        }
        
        if entity_type == "companies":
            entity_type = "company"

        return self.call("%s/set" % entity_type, json_to_pass)
    
    # Works with contacts, leads, companies, tasks. Doesn't work with customers!
    def get_entity(self, entity_type, **kwargs):
        if not entity_type in entity_optional_params and entity_type != "tasks":
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        if entity_type == "customers":
            raise AmoException("Get entity doesn't work with customers!", None)
            
        optional_params = ["if-modified-since", "limit_rows", "limit_offset",
            "id", "query", "responsible_user_id", "type", "status", "element_id"]
            
        params_to_pass = {}
        
        for (key, value) in kwargs.items():
            if key in optional_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
                
        if entity_type == "companies":
            entity_type = "company"
        response = self.call("%s/list" % entity_type, params_to_pass)
        
        return response
    
    #TODO: This should belong different class        
    def rotate_user(self, department_id):
        if not isinstance(department_id, int):
            raise AmoException("Department id should be an integer!", None) 
        
        users_cache = self.user.last_user_cache
            
        if not "-1" in users_cache:
            users_cache["-1"] = -1
        if not "0" in users_cache:
            users_cache["0"] = -1
            
        cache = self.user.cache
        groups = cache["account"]["groups"]
        for group in groups:
            if not str(group["id"]) in users_cache:
                users_cache[str(group["id"])] = -1
                
        if str(department_id) in users_cache:
            prev_user_id = int(users_cache[str(department_id)])
        elif department_id < 0:
            prev_user_id = int(users_cache[str(-1)])
        else:
            message = "Unknown department_id <%s>" % department_id
            raise AmoException(message, None) 
         
        department_users_id = [int(user["id"]) for user in cache["account"]["users"] 
            if  user["rights_contact_view"] != "D" and 
                (department_id < 0 or user["group_id"] == department_id)]
        department_users_id.sort()
        min_user_id = department_users_id[0]
        greater_users_id = [user_id for user_id in department_users_id 
            if user_id > prev_user_id]
        if not greater_users_id:
            next_user_id = min_user_id
        else:
            next_user_id = greater_users_id[0]
                        
        if department_id >= 0:
            users_cache[str(department_id)] = next_user_id
        else:
            users_cache["-1"] = next_user_id
        
        self.user.last_user_cache = users_cache
    
    # Elemnt type 1 - contact, 2 - lead, 3 - company
    def add_task(self, element_id, element_type, task_type, text, complete_till,
        **kwargs):
            
        self.update_cache()
        cache = self.user.cache
        
        task_types = [t for t in cache["account"]["task_types"] 
            if t["code"] == task_type or t["id"] == task_type or t["name"] == task_type]
        if not task_types:
            message = "Unknown task_type <%s>" % task_type
            raise AmoException(message, None) 
            
        if not element_type in [1,2,3, "contacts", "leads", "companies"]:
            message = "Unknown element_type <%s>" % element_type
            raise AmoException(message, None) 
        
        if not isinstance(element_type, int):
            element_type = {"contacts":1, "leads":2, "companies":3}[element_type]
            
        task_type = task_types[0]["id"]
            
        params_to_pass = {
            "element_id" : element_id,
            "element_type" : element_type,
            "task_type" : task_type,
            "text" : text,
            "complete_till" : complete_till,
            "created_user_id" : 0
        }
        
        task_optional_params = ["date_create", "last_modified", "status",
            "responsible_user_id", "created_user_id"]
            
        for (key, value) in kwargs.items():
            if key in task_optional_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
                
        json_to_pass = {
            "request" : {
                "tasks" : {
                    "add" : [params_to_pass]
                }
            }
        }
        
        # print(json.dumps(json_to_pass, ensure_ascii=False))
        return self.call("tasks/set", json_to_pass)
        
    def update_task(self, id, last_modified, text, **kwargs):
        params_to_pass = {
            "id" : id,
            "last_modified" : last_modified,
            "text" : text
        }
        
        task_optional_params = ["date_create", "last_modified", "status",
            "responsible_user_id", "created_user_id", "complete_till", "task_type"]
            
        if "task_type" in kwargs:
            self.update_cache()
            cache = self.user.cache
            task_type = kwargs["task_type"]
            task_types = [t for t in cache["account"]["task_types"] 
                if t["code"] == task_type or t["id"] == task_type or t["name"] == task_type]
            if not task_types:
                message = "Unknown task_type <%s>" % task_type
                raise AmoException(message, None) 
            
            task_type = task_types[0]["id"]
                
            params_to_pass["task_type"] = task_type
            
        for (key, value) in kwargs.items():
            if key in task_optional_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
                
        json_to_pass = {
            "request" : {
                "tasks" : {
                    "update" : [params_to_pass]
                }
            }
        }
        
        return self.call("tasks/set", json_to_pass)
    
    # Look up for filter param in here https://developers.amocrm.ru/rest_api/customers/list.php
    # TODO: filter is not working doesn't know why :( https://www.youtube.com/watch?v=VJfK-QLv27o
    def get_customers(self, **kwargs):
        optional_params = ["limit_rows", "limit_offset", "PAGEN_1", "filter"]
            
        params_to_pass = {}
        
        for (key, value) in kwargs.items():
            if key in optional_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
                
        response = self.call("customers/list", params_to_pass)
        
        return response
        
    # First entity will have priority. Waiting for lists of custom fields
    def unite_entities(self, entity_type, first_entity, second_entity):
        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
            
        if not isinstance(first_entity, list) or not isinstance(second_entity, list):
            raise AmoException("Waiting list as an entity!", None)
        
        self.update_cache()
        fields_cache = self.user.fields_cache
        
        united_entity = []
        for first_entity_field in first_entity:
            first_entity_id = first_entity_field["id"]
            if not first_entity_id in fields_cache[entity_type]:
                message = "Unknown field id <%s>" % first_entity_id
                raise AmoException(message, None)
            
            cached_field = fields_cache[entity_type][first_entity_id]
            
            if cached_field["multiple"] == "Y" or "enums" in cached_field:
                new_field = first_entity_field
                for second_entity_field in second_entity:
                    if first_entity_field["id"] == second_entity_field["id"]:
                        for v2 in second_entity_field["values"]:
                            new_value = True
                            for v1 in first_entity_field["values"]:
                                if v1["value"] == v2["value"]:
                                    new_value = False
                            if new_value:
                                new_field["values"].append(v2)
                united_entity.append(new_field)
                                    
            else:
                united_entity.append(first_entity_field)
                
        for second_entity_field in second_entity:
            new_id = True
            for u_field in united_entity:
                if u_field["id"] == second_entity_field["id"]:
                    new_id = False
            if new_id:
                united_entity.append(second_entity_field)
                
        return united_entity
    
    # TODO: complete these function    
    def send_order_data(self, lead_data=[], contact_data=[], company_data=[], tags=[]):
        if not lead_data and not contact_data and not company_data:
            raise AmoException("Please send some data!", None)


