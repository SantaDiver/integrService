entity_optional_params = {
    "contacts" : ["tags", "created_at", "updated_at", "created_by", 
        "company_name", "leads_id", "customers_id", "company_id"],
    "leads" : ["tags", "created_at", "updated_at", "status_id", "pipeline_id",
        "sale", "contacts_id", "company_id"],
    "companies" : ["tags", "created_at", "updated_at", "created_by", "leads_id",
        "customers_id", "contacts_id"],
    "customers" : ["tags", "next_date", "created_at", "updated_at", "created_by",
        "next_price", "periodicity", "period_id", "contacts_id", "company_id",]
}

update_optional_params = {
    "contacts" : ["name", "unlink", "responsible_user_id"],
    "leads" : ["name", "unlink", "responsible_user_id"],
    "companies" : ["name", "unlink", "responsible_user_id"],
    "customers" : ["name", "unlink", "responsible_user_id"]
}

get_optional_params = {
    "contacts" : ["id[]", "id", "limit_rows", "limit_offset", 
        "responsible_user_id", "query"],
    "leads" : ["id[]", "limit_rows", "limit_offset", "id", "query", 
        "responsible_user_id", "status"],
    "companies" : ["id[]", "limit_rows", "limit_offset", "id", "query", 
        "responsible_user_id"],
    "tasks" : ["id[]", "id", "limit_rows", "limit_offset", "element_id", 
        "responsible_user_id", "type"]
}

one_by_one = "По очереди"
zero_department = "Отдел продаж"
not_chosen = "Не выбрано"
ening_statuses = [142, 143]
succes_status = 142