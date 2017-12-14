entity_optional_params = {
    "contacts" : ["tags", "created_at", "updated_at", "created_by", 
        "company_name", "leads_id", "customers_id", "company_id"],
    "leads" : ["tags", "created_at", "updated_at", "status_id", "pipeline_id",
        "sale", "contacts_id", "company_id"],
    "companies" : ["tags", "created_at", "updated_at", "created_by", "leads_id",
        "customers_id", "contacts_id"],
    "customers" : ["tags", ]
}

update_optional_params = {
    "contacts" : ["name", "unlink", "responsible_user_id"],
    "leads" : ["name", "unlink", "responsible_user_id"],
    "companies" : ["name", "unlink", "responsible_user_id"],
    "customers" : ["name", ]
}

get_optional_params = {
    "contacts" : ["id[]", "id", "limit_rows", "limit_offset", 
        "responsible_user_id", "query"],
    "leads" : ["id[]", "limit_rows", "limit_offset", "id", "query", 
        "responsible_user_id", "status"],
    "companies" : ["id[]"],
    "customers" : ["id[]"],
    "tasks" : ["id[]"]
}