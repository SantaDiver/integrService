# TODO: add functiond for getting/adding/updateing with useful names
# TODO: change with new API

import json
import requests
import time
from pprint import pprint
import os.path
import sys

from utils import entity_optional_params
from utils import update_optional_params
from utils import get_optional_params
from utils import succes_status

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
            
            
    def call(self, request, request_method, params={}):
        url = "https://%s.amocrm.ru/%s" % (
                self.cfg["subdomain"], request)

        if request_method == "GET":
            response = self.request.get(url, params = params)
        elif request_method == "POST":
            response = self.request.post(url, json = params)
        else:
            raise AmoException("Unknown request method %s" % request_method, None)
            
        if (response.status_code == 401):
            self._auth()
            if request_method == "GET":
                response = self.request.get(url, params = params)
            else:
                response = self.request.post(url, json = params)
            
        if (response.status_code != 200 and not (response.status_code == 204 and
            response.reason=="No Content")):

            message = "Status code is %s" % response.status_code
            raise AmoException(message, response)
        
        if (response.status_code == 204 and response.reason=="No Content"):
            return {
                "_embedded" : {
                    "items" : []
                }
            }
            
        return response.json()
        
    def cache_special_type_fields(self, type_of_element, cache):
        result_cache = {}
        if not cache["_embedded"]["custom_fields"][type_of_element]:
            return {}
            
        for field_id, field in cache["_embedded"]["custom_fields"][type_of_element].items():
            result_cache[field["name"]] = field
            result_cache[field_id] = field
            
        return result_cache
    
    # Doesn't work with catalog elemtns
    def cache_fields(self):
        cache = self.user.cache
        fields_cache = {}
        type_of_elements = ["contacts", "leads", "companies", "customers"]
            
        for type_of_element in type_of_elements:
            fields_cache[type_of_element] = self.cache_special_type_fields(
                type_of_element, cache)
        
        self.user.fields_cache = fields_cache
    
    def force_to_update_cache(self):
        resp = self.call("api/v2/account", "GET", {
            "with" : "custom_fields,users,pipelines,groups,note_types,task_types"
        })
        resp["timestamp"] = time.time()
        self.user.cache = resp
                
    def update_cache(self):
        cache = self.user.cache
        if not "timestamp" in cache:
            self.force_to_update_cache()
            self.cache_fields()
        elif time.time() - cache["timestamp"] > int(self.cfg["cache_ttl"]):
            self.force_to_update_cache()
            self.cache_fields()
    
    def translate_fields(self, fields, type_of_element):
        self.update_cache()
        fields_cache = self.user.fields_cache
        translated_fields = []
        for (name, value) in fields.items():
            if not value:
                continue
                # raise AmoException("Empty field value!", None)
            
            field_from_cache = fields_cache[type_of_element][name]
           
            translated_field = {
                "id" : field_from_cache["id"],
                "values" : []
            }

            if field_from_cache["is_multiple"]:
                if not type(value) is list:
                    value = [value,]
                for single_value in value:
                    for (enum, subvalue) in single_value.items():
                        translated_field["values"].append({
                            "value" : subvalue,
                            "enum" : enum
                        })
            
            # TODO: сделать, чтобы работало с Адресами
            # Тут костыль
            # elif "адрес" in name.lower():
            #     for (subtype, subvalue) in value.items():
            #         translated_field["values"].append({
            #             "subtype" : subtype,
            #             "value" : subvalue
            #         })
                
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
        translate = True, call=True, **kwargs):
            
        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        if translate:
            translated_fields = self.translate_fields(custom_fields, entity_type)
        else:
            translated_fields = custom_fields
            
        params_to_pass = {
            "name" : name,
            "responsible_user_id" : responsible_user_id,
            "custom_fields" : translated_fields,
        }
        
        if entity_type in ["contacts", "companies"]:
            params_to_pass["created_by"] = 0
            
        for (key, value) in kwargs.items():
            if key in entity_optional_params[entity_type]:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        if not call:
            return params_to_pass
        
        json_to_pass = {
            "add" : [params_to_pass]
        }

        return self.call("api/v2/%s" % entity_type, "POST", json_to_pass)
    
    # Works with contacts, leads, companies, customers. Doesn't work with tasks!
    def update_entity(self, entity_type, entity_id, translate=True, call=True, 
        updated_at=time.time(), **kwargs):
            
        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        params_to_pass = {
            "id" : entity_id,
            "updated_at" : updated_at
        }
        
        if "custom_fields" in kwargs:
            if translate:
                params_to_pass["custom_fields"] = self.translate_fields(
                    kwargs["custom_fields"], entity_type)
            else:
                params_to_pass["custom_fields"] = kwargs["custom_fields"]
        
        for (key, value) in kwargs.items():
            if key in entity_optional_params[entity_type] or key in update_optional_params[entity_type]:
                params_to_pass[key] = value
            elif not key in ["custom_fields"]:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        if not call:
            return params_to_pass
        
        json_to_pass = {
            "update" : [params_to_pass]
        }

        return self.call("api/v2/%s" % entity_type, "POST", json_to_pass)
    
    # Works with contacts, leads, companies, tasks. Doesn't work with customers!
    def get_entity(self, entity_type, **kwargs):
        if not entity_type in get_optional_params and entity_type != "tasks":
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        if entity_type == "customers":
            raise AmoException("Get entity doesn't work with customers!", None)
            
        params_to_pass = {}
        
        for (key, value) in kwargs.items():
            if key in get_optional_params[entity_type]:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
                
        response = self.call("api/v2/%s" % entity_type, "GET", params_to_pass)
            
        return response
    
    #TODO: This should belong different class
    # TODO: add allowed users list in config
    # TODO: add weights to users
    def rotate_user(self, department_id):
        if not isinstance(department_id, int):
            raise AmoException("Department id should be an integer!", None) 
        
        self.update_cache()
        users_cache = self.user.last_user_cache
            
        if not "-1" in users_cache:
            users_cache["-1"] = -1
        if not "0" in users_cache:
            users_cache["0"] = -1
            
        cache = self.user.cache
        groups = cache["_embedded"]["groups"]
        for group_id in groups:
            if not str(group_id) in users_cache:
                users_cache[str(group_id)] = -1
                
        if str(department_id) in users_cache:
            prev_user_id = int(users_cache[str(department_id)])
        elif department_id < 0:
            prev_user_id = int(users_cache[str(-1)])
        else:
            message = "Unknown department_id <%s>" % department_id
            raise AmoException(message, None) 
         
        department_users_id = [int(user_id) for user_id, user in 
            cache["_embedded"]["users"].items()
            if (department_id < 0 or user["group_id"] == department_id)]
            
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
        
        return users_cache[str(department_id)]
    
    # Elemnt type 1 - contact, 2 - lead, 3 - company
    def add_task(self, element_id, element_type, task_type, text, complete_till_at,
        responsible_user_id, call=True, **kwargs):
            
        self.update_cache()
        cache = self.user.cache
        
        task_types = [t_id for t_id, t in cache["_embedded"]["task_types"].items() 
            if t["id"] == task_type or t["name"] == task_type]
        if not task_types:
            message = "Unknown task_type <%s>" % task_type
            raise AmoException(message, None) 
            
        if not element_type in [1,2,3,12, "contacts", "leads", "companies", "customers"]:
            message = "Unknown element_type <%s>" % element_type
            raise AmoException(message, None) 
        
        if not isinstance(element_type, int):
            element_type = {"contacts":1, "leads":2, "companies":3, "customers":12}[element_type]
            
        task_type = task_types[0]
            
        params_to_pass = {
            "element_id" : element_id,
            "element_type" : element_type,
            "task_type" : task_type,
            "text" : text,
            "complete_till_at" : complete_till_at,
            "responsible_user_id" : responsible_user_id,
            "created_by" : 0
        }
        
        task_optional_params = ["created_at", "updated_at", "is_completed",
            "created_by"]
            
        for (key, value) in kwargs.items():
            if key in task_optional_params:
                params_to_pass[key] = value
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
         
        if not call:
            return params_to_pass
               
        json_to_pass = {
            "add" : [params_to_pass]
        }
        
        return self.call("api/v2/tasks", "POST", json_to_pass)
        
    def update_task(self, task_id, updated_at, text, call=True, **kwargs):
        params_to_pass = {
            "id" : task_id,
            "updated_at" : updated_at,
            "text" : text
        }
        
        task_optional_params = ["element_id", "element_type", "task_type",
            "complete_till_at", "responsible_user_id", "created_by", 
            "created_at", "is_completed"]
            
        if "task_type" in kwargs:
            self.update_cache()
            cache = self.user.cache
            task_type = kwargs["task_type"]
            task_types = [t_id for t_id, t in cache["_embedded"]["task_types"].items() 
                if t["id"] == task_type or t["name"] == task_type]
            if not task_types:
                message = "Unknown task_type <%s>" % task_type
                raise AmoException(message, None) 
            
            task_type = task_types[0]
                
            params_to_pass["task_type"] = task_type
            
        for (key, value) in kwargs.items():
            if key in task_optional_params:
                params_to_pass[key] = value
            elif not key in ["task_type"]:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        if not call:
            return params_to_pass
        
        json_to_pass = {
            "update" : [params_to_pass]
        }
        
        return self.call("api/v2/tasks", "POST", json_to_pass)
    
    # Why the fuck they want json with get parametres https://www.youtube.com/watch?v=VJfK-QLv27o
    # TODO: make filter work not only with id
    def get_customers(self, **kwargs):
        optional_params = []
            
        params_to_pass = {}
        
        for (key, value) in kwargs.items():
            if key in optional_params:
                params_to_pass[key] = value
            elif "id" in kwargs:
                params_to_pass["filter[id][]"] = kwargs["id"]
            else:
                message = "Param <%s> is incorrect" % key
                raise AmoException(message, None)
        
        response = self.call("api/v2/customers", "GET", params_to_pass)
        
        return response
    
    # TODO: return lost difference
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
            first_entity_id = str(first_entity_field["id"])
            
            if not first_entity_id in fields_cache[entity_type]:
                message = "Unknown field id <%s>" % first_entity_id
                raise AmoException(message, None)
            
            cached_field = fields_cache[entity_type][first_entity_id]
            
            if cached_field["is_multiple"] or "enums" in cached_field:
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
    
    # Supports additional_data_to_query
    # Example:
    #     additional_data_to_query = {
    #       "contacts" : {
    #         "Тип" : ["Вар4", "Вар3"]
    #     }
    # }
    def find_duplicates(self, entity, entity_type, fields_to_find_duplicates, 
        **kwargs):

        if not entity_type in entity_optional_params:
            message = "Unknown entity type <%s>" % entity_type
            raise AmoException(message, None)
        
        duplicates = []
        self.update_cache()
        fields_cache = self.user.fields_cache[entity_type]
        
        for field in fields_to_find_duplicates:
            if not field in fields_cache:
                message = "Field <%s> is incorrect" % field
                raise AmoException(message, None)
            if field in entity:
                if not type(entity[field]) is list:
                    entity[field] = [entity[field],]
                
                if not fields_cache[field]["is_multiple"]:
                    for entity_field in entity[field]:
                        duplicates += self.get_entity(entity_type, 
                            query=entity_field)["_embedded"]["items"]
                        
                else:
                    for entity_field in entity[field]:
                        for enum in fields_cache[field]["enums"]:
                            enum_name = fields_cache[field]["enums"][enum]
                            
                            if enum in entity_field:
                                duplicates += self.get_entity(entity_type, 
                                    query=entity_field[enum])["_embedded"]["items"]
                            
                            if enum_name in entity_field:
                                duplicates += self.get_entity(entity_type, 
                                    query=entity_field[enum_name])["_embedded"]["items"]
                                
        if "additional_data_to_query" in kwargs:
            if entity_type in kwargs["additional_data_to_query"]:
                duplicates += self.find_duplicates(
                    kwargs["additional_data_to_query"][entity_type], entity_type, 
                    fields_to_find_duplicates)
                                
        return duplicates
    
    
    def get_not_closed_leads(self, entities):
        leads_id = []
        for entity in entities:
            if "id" in entity["leads"]:
                leads_id += entity["leads"]["id"]
            
        if not leads_id:
            return []
            
        internal_kwargs = {"id[]" : leads_id}
        leads = self.get_entity("leads", **internal_kwargs)["_embedded"]["items"]
        
        not_closed_leads = [lead for lead in leads 
            if lead["closed_at"] == 0 and not lead["is_deleted"]]
        
        return not_closed_leads
        
    def get_not_closed_customers(self, entities):
        customers_id = []
        for entity in entities:
            if "id" in entity["customers"]:
                customers_id += entity["customers"]["id"]
            
        if not customers_id:
            return []
            
        customers = self.get_customers(id=customers_id)["_embedded"]["items"]
        
        not_closed_customers = [customer for customer in customers 
            if customer["next_date"] != 0 and not customer["is_deleted"]]
        
        return not_closed_customers
        
    def get_succes_leads(self, entities):
        leads_id = []
        for entity in entities:
            if "id" in entity["leads"]:
                leads_id += entity["leads"]["id"]
            
        if not leads_id:
            return []
            
        internal_kwargs = {"id[]" : leads_id}
        leads = self.get_entity("leads", **internal_kwargs)["_embedded"]["items"]
        
        # Magic: 142 is Succes status in ANY pipline in ANY account
        # https://www.youtube.com/watch?v=DCsMXYgLXqs
        reccurent = [lead for lead in leads 
            if lead["status_id"] == succes_status and not lead["is_deleted"]]
        
        return reccurent
    
    
    # TODO: add finding duplicates with different responsible user
    # TODO: Add message if duplicates > 1
    # TODO: Add lost update difference (contact/company and lead)
    
    ###
    
    # Entity data = { tags=..., custom_fields=..., name=...}
    # responsible_user_id or department_id required
    # additional_data_to_query (look at find duplicates function)
    # pipelines = {
    #   status_for_new = ... , 
    #   status_for_rec = ...
    #} 
    # tag_for_rec = str
    
    ###
    def send_order_data(self, lead_data={}, contact_data={}, company_data={}, 
        generate_tasks_for_rec=False, department_id=-1, **kwargs):
            
        if not lead_data and not contact_data and not company_data:
            raise AmoException("Please send some data!", None)
            
        if generate_tasks_for_rec and (not "rec_lead_task_text" in self.cfg or
            not "time_to_complete_rec_task" in self.cfg):
            raise AmoException("CFG params are needed to generate rec tasks!", None)
        
        self.update_cache()            
        contact_duplicates = []
        company_duplicates = []
        if "fields_to_check_dups" in self.cfg:
            if contact_data and "contacts" in self.cfg["fields_to_check_dups"]:
                contact_duplicates += self.find_duplicates(contact_data["custom_fields"], 
                    "contacts", self.cfg["fields_to_check_dups"]["contacts"], **kwargs)
            
            if company_data and "companies" in self.cfg["fields_to_check_dups"]:
                company_duplicates += self.find_duplicates(company_data["custom_fields"], 
                    "companies", self.cfg["fields_to_check_dups"]["companies"], **kwargs)
        
        if contact_duplicates:
            responsible_user_id = contact_duplicates[0]["responsible_user_id"]
        elif company_duplicates:
            responsible_user_id = company_duplicates[0]["responsible_user_id"]
        elif "responsible_user_id" in kwargs:
            responsible_user_id = kwargs["responsible_user_id"]
        else:
            responsible_user_id = self.rotate_user(department_id)
        
        if contact_duplicates:
            united_data = self.unite_entities(
                "contacts", 
                contact_duplicates[0]["custom_fields"],
                self.translate_fields(contact_data["custom_fields"], "contacts")
            )
            tags = contact_data["tags"]
            dup_tags = [tag["name"] for tag in contact_duplicates[0]["tags"]]
            
            united_tags = ",".join(dup_tags) + "," + tags
                    
            self.update_entity(
                "contacts", 
                contact_duplicates[0]["id"], 
                translate = False,
                call = True,
                updated_at = time.time(),
                custom_fields = united_data,
                tags = united_tags
            ) 
            
            contact_id = contact_duplicates[0]["id"]
        
        elif contact_data:
            contact_id = self.add_entity(
                    entity_type = "contacts", 
                    name = contact_data["name"], 
                    responsible_user_id = responsible_user_id, 
                    custom_fields = contact_data["custom_fields"],
                    tags = contact_data["tags"]
            )["_embedded"]["items"][0]["id"]
            
        if company_duplicates:
            united_data = self.unite_entities(
                "companies", 
                company_duplicates[0]["custom_fields"],
                self.translate_fields(company_data["custom_fields"], "companies")
            )
            tags = company_data["tags"]
            dup_tags = [tag["name"] for tag in company_duplicates[0]["tags"]]
            
            united_tags = ",".join(dup_tags) + "," + tags
            
            internal_kwargs = {}
            if contact_data:
                 internal_kwargs["contacts_id"] = [contact_id]
                
            self.update_entity(
                "companies", 
                company_duplicates[0]["id"], 
                translate = False,
                call = True,
                updated_at = time.time(),
                custom_fields = united_data,
                tags = united_tags,
                **internal_kwargs
            )  
            
            company_id = company_duplicates[0]["id"]
            
        elif company_data:
            internal_kwargs = {}
            if contact_data:
                 internal_kwargs["contacts_id"] = [contact_id]
            
            company_id = self.add_entity(
                    entity_type = "companies", 
                    name = contact_data["name"], 
                    responsible_user_id = responsible_user_id, 
                    custom_fields = company_data["custom_fields"],
                    tags = company_data["tags"],
                    **internal_kwargs
            )["_embedded"]["items"][0]["id"]
            
        if lead_data:
            not_closed_leads = []
            not_closed_customers = []
            if contact_duplicates:
                not_closed_leads += self.get_not_closed_leads(contact_duplicates)
                not_closed_customers += self.get_not_closed_customers(contact_duplicates)
            if company_duplicates:
                not_closed_leads += self.get_not_closed_leads(company_duplicates)
                not_closed_customers += self.get_not_closed_customers(company_duplicates)
                
            if not not_closed_leads and not not_closed_customers:
                internal_kwargs = {}
                if contact_data:
                     internal_kwargs["contacts_id"] = [contact_id]
                if company_data:
                     internal_kwargs["company_id"] = [company_id]
                     
                if "pipelines" in kwargs:
                    if self.get_succes_leads(contact_duplicates) or self.get_succes_leads(company_duplicates):
                        
                        if "status_for_rec" in kwargs["pipelines"]:
                            internal_kwargs["status_id"] = kwargs["pipelines"]["status_for_rec"]
                        if "tag_for_rec" in kwargs:
                            lead_data["tags"] += "," + kwargs["tag_for_rec"]
                            
                    elif "status_for_new" in kwargs["pipelines"]:
                        internal_kwargs["status_id"] = kwargs["pipelines"]["status_for_new"]
                        
                lead_id = self.add_entity(
                    entity_type = "leads", 
                    name = lead_data["name"], 
                    responsible_user_id = responsible_user_id, 
                    custom_fields = lead_data["custom_fields"],
                    tags = lead_data["tags"],
                    **internal_kwargs
                )["_embedded"]["items"][0]["id"]
                    
            elif generate_tasks_for_rec:
                # Already check cfg to contain these keys
                if not_closed_leads:
                    element_id = not_closed_leads[0]["id"]
                    element_type = "leads"
                else:
                    element_id = not_closed_customers[0]["id"]
                    element_type = "customers"
                    
                self.add_task(
                    element_id = element_id,
                    element_type = element_type,
                    task_type = "Звонок",
                    responsible_user_id = not_closed_customers[0]["responsible_user_id"],
                    text = self.cfg["rec_lead_task_text"],
                    complete_till_at = time.time()+self.cfg["time_to_complete_rec_task"]
                )
            
                lead_id = element_id
                
        data_to_return = {}
        if lead_data:
            data_to_return["lead_id"] = lead_id
        if contact_data:
            data_to_return["contact_id"] = contact_id
        if company_data:
            data_to_return["company_id"] = company_id
            
        return data_to_return
        
            
        
            
        
                    
                    

