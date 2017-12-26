from dadata.plugins.django import DjangoDaDataClient
from utils import one_by_one, not_chosen, default_name

def conform_fields(conformity, data):
    data_to_send = {
        'contact_data' : {},
        'company_data' : {},
        'lead_data' : {}
    }
    
    for data_type in ['contact_data', 'company_data', 'lead_data']:
        if data_type in conformity:
            if 'name' in conformity and conformity['name'] in data:
                data_to_send[data_type]['name'] = data[conformity['name']]
            elif 'default_name' in conformity:
                data_to_send[data_type]['name'] = conformity['default_name']
            elif data_type == 'lead_data':
                data_to_send[data_type]['name'] = None
            else:
                data_to_send[data_type]['name'] = default_name
                
            data_to_send[data_type]['custom_fields'] = {}
            for field, field_alias in conformity.items():
                if not field in ['name', 'default_name'] and field_alias in data:
                    if not field in ['Телефон', 'Email']:
                        data_to_send[data_type]['custom_fields'][field] = data[field_alias]
                    else:
                        data_to_send[data_type]['custom_fields'][field] = {
                            'WORK' : data[field_alias]
                        }
                        
            if 'tags' in conformity:
                data_to_send[data_type]['tags'] = conformity['tags']
    
    generate_tasks_for_rec = False
    if 'generate_tasks_for_rec' in conformity:
        generate_tasks_for_rec = conformity['generate_tasks_for_rec']
    
    department_id = -1
    if 'department_id' in conformity and conformity['department_id'] != not_chosen:
        department_id = conformity['department_id']
        
    internal_kwargs = {'additional_data_to_query' : {}}
    if 'responsible_user_id' in conformity and conformity['responsible_user_id'] != one_by_one:
        internal_kwargs['responsible_user_id'] = conformity['responsible_user_id']
        
    additional_params = ['pipelines', 'tag_for_rec', 'time_to_complete_rec_task',
        'rec_lead_task_text', 'fields_to_check_dups']
    for param in additional_params:
       if param in conformity: 
           internal_kwargs[param] = conformity[param]
        
    if 'dadata_phone_check' in conformity and conformity['dadata_phone_check']:
        client = DjangoDaDataClient()
        internal_kwargs['additional_data_to_query']['Телефон'] = []
        
        for data_type in ['contact_data', 'company_data']:
            if 'custom_fields' in data_to_send[data_type] and 'Телефон' in \
                data_to_send[data_type]['custom_fields']:
                
                for key,value in data_to_send[data_type]['custom_fields']['Телефон'].items():
                    client.phone = value
                    client.phone.request()
                    
                    if client.result.phone != None:
                        data_to_send[data_type]['custom_fields']['Телефон'][key] = client.result.phone
                    
                    if client.result.number != None:
                        internal_kwargs['additional_data_to_query']['Телефон'].append({
                            'WORK' : client.result.number
                        })
                        
    return (data_to_send, generate_tasks_for_rec, department_id, internal_kwargs)
    
def find_pipline_id(pipelines, name):
    for pipeline_id, pipeline in pipelines.items():
        for status_id, status in pipeline['statuses'].items():
            if pipeline['name'] == name.split('/')[0] and status['name'] == name.split('/')[1]:
                return status_id