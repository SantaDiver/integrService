from dadata.plugins.django import DjangoDaDataClient

def conform_fields(conformity, data):
    data_to_send = {
        "contact_data" : {},
        "company_data" : {},
        "lead_data" : {}
    }
    
    for data_type in ["contact_data", "company_data", "lead_data"]:
        if data_type in conformity:
            if "name" in conformity and conformity["name"] in data:
                data_to_send[data_type]["name"] = data[conformity["name"]]
            elif "default_name" in conformity:
                data_to_send[data_type]["name"] = conformity["default_name"]
            elif data_type == "lead_data":
                data_to_send[data_type]["name"] = None
            else:
                raise Exception("No name for contact")
                
            data_to_send[data_type]["custom_fields"] = {}
            for field, field_alias in conformity.items():
                if not field in ["name", "default_name"] and field_alias in data:
                    if not field in ["Телефон", "Email"]:
                        data_to_send[data_type]["custom_fields"][field] = data[field_alias]
                    else:
                        data_to_send[data_type]["custom_fields"][field] = {
                            "WORK" : data[field_alias]
                        }
                        
            if "tags" in conformity:
                data_to_send[data_type]["tags"] = conformity["tags"]
    
    generate_tasks_for_rec = False
    if "generate_tasks_for_rec" in conformity:
        generate_tasks_for_rec = conformity["generate_tasks_for_rec"]
    
    department_id = -1
    if "department_id" in conformity:
        department_id = conformity["department_id"]
        
    internal_kwargs = {"additional_data_to_query" : {}}
    if "pipelines" in conformity:
        internal_kwargs["pipelines"] = conformity["pipelines"]
    if "responsible_user_id" in conformity:
        internal_kwargs["responsible_user_id"] = conformity["responsible_user_id"]
    if "tag_for_rec" in conformity:
        internal_kwargs["tag_for_rec"] = conformity["tag_for_rec"]
        
    if "dadata_phone_check" in conformity and conformity["dadata_phone_check"]:
        client = DjangoDaDataClient()
        internal_kwargs["additional_data_to_query"]["Телефон"] = []
        
        for data_type in ["contact_data", "company_data"]:
            if "custom_fields" in data_to_send[data_type] and "Телефон" in \
                data_to_send[data_type]["custom_fields"]:
                
                for key,value in data_to_send[data_type]["custom_fields"]["Телефон"].items():
                    client.phone = value
                    client.phone.request()
                    
                    if client.result.phone != None:
                        data_to_send[data_type]["custom_fields"]["Телефон"][key] = client.result.phone
                    
                    if client.result.number != None:
                        internal_kwargs["additional_data_to_query"]["Телефон"].append({
                            "WORK" : client.result.number
                        })
                        
    return (data_to_send, generate_tasks_for_rec, department_id, internal_kwargs)