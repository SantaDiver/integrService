import sys
import json
import logging
import time
from pprint import pprint

from amoIntegr import AmoIntegr
from amoException import AmoException

if __name__ == '__main__':
    try:
        api = AmoIntegr('./configs/config.json')

        contact_data = {
            "Поле 5" : 911,
            "Должность" : "Some",
            "Телефон" : {"WORK" : "123", "MOB" : "098"},
            "Тип" : ["вар1"],
            "Email" : {"WORK" : "email-mail"}
        }
        
        lead_data = {
            "что-то" : 1000000
        }
        
        

        api.add_entity("leads", "Test123098", 1408894, lead_data, price=1011)
        # api.add_entity("contacts", "Testttttttttttttttttttttttttt", 1408894, contact_data)
        # api.update_entity("leads", 12127855, time.time(), responsible_user_id=1408894)
        # api.add_entity("companies", "Test123098", 1408894, {})
        # pprint(api.add_task(12127855, "leads", "Встреча", "The text", time.time()+900))
        # api.update_task(14987033, time.time(), "Новый текст", task_type="Звонок")
        # resp = api.get_entity("tasks", element_id=12127855)
        # pprint(resp)
        # pprint(api.get_customers(filter={"main_user":845532}))
        
        # e1 = api.get_entity("contacts", id=24546371, type="contact")["contacts"][0]["custom_fields"]
        # e2 = api.translate_fields(contact_data, "contacts")
        
        # pprint(e1)
        # pprint("-----------------------------------------")
        # pprint(e2)
        # pprint("-----------------------------------------")
        
        # api.unite_entities("contacts", e1, e2)
        api.send_order_data([1,2])
        
    except AmoException as e:
        print('AmoException raised:', e.message)
        print(e.response)
        logging.exception("AmoException")
    except:
        print ('Raised unexpected exception:', sys.exc_info()[0])
        logging.exception("Unexpected exception")
        raise