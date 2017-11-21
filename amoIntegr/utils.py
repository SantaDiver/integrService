request_method_map = {
    "accounts/current" : "GET",
    "contacts/set" : "POST",
    "contacts/list" : "GET",
    "contacts/links" : "GET",
    "leads/set" : "POST",
    "leads/list" : "GET",
    "company/set" : "POST",
    "company/list" : "GET",
    "customers/set" : "POST",
    "customers/list" : "GET",
    "transactions/set" : "POST",
    "transactions/list" : "GET",
    "tasks/set" : "POST",
    "tasks/list" : "GET",
    "notes/set" : "POST",
    "notes/list" : "GET",
    "fields/set" : "POST",
    "calls/add" : "POST",
    "unsorted/list" : "GET",
    "unsorted/get_all_summary" : "GET",
    "unsorted/accept" : "POST",
    "unsorted/decline" : "POST",
    "unsorted/add" : "POST",
    "webhooks/list" : "GET",
    "webhooks/subscribe" : "POST",
    "webhooks/unsubscribe" : "POST",
    "pipelines/list" : "GET",
    "pipelines/set" : "POST",
    "pipelines/delete" : "POST",
    "customers_periods/list" : "GET",
    "customers_periods/set" : "POST",
    "widgets/list" : "GET",
    "widgets/set" : "POST",
    "catalogs/list" : "GET",
    "catalogs/set" : "POST",
    "catalog_elements/list" : "GET",
    "catalog_elements/set" : "POST",
    "links/list" : "GET",
    "links/set" : "POST",
    "elements/sync" : "POST"
}

def get_method_by_request(request):
    if not request in request_method_map:
        raise BaseException("No such api request in get_method_by_request")
    return request_method_map[request]

entity_optional_params = {
    "contacts" : ["tags", "created_user_id", "linked_leads_id",
        "company_name", "linked_company_id"],
    "leads" : ["date_create", "last_modified", "status_id", "pipeline_id",
        "price", "created_user_id", "request_id", "linked_company_id", 
        "tags"],
    "companies" : ["tags", "created_user_id", "linked_leads_id"],
    "customers" : ["tags", "next_date", "next_price", "periodicity"]
}