import requests
import os
import json

API_KEY = os.environ['API_KEY']
SERVICE_ID = ""

url = "https://cloudbilling.googleapis.com/v1/services?key=" + API_KEY
service_url = "https://cloudbilling.googleapis.com/v1/services/" + SERVICE_ID + "/skus?key=" + API_KEY

def save_data(json_data, service_name):
    with open('./GCP_DATA/{} Data.json'.format(service_name), 'w') as json_file:
        json.dump(json_data, json_file)


def get_data(url,service_url):
    service_data = get_services_index(url)
    services = service_data["services"]
    for service in services:
        SERVICE_ID = service["serviceId"]
        json_data = requests.get(service_url).json()
        save_data(json_data,service["displayName"])

    if json_data["NextPageLink"]:
        url = json_data["NextPageLink"]
        get_data(url)

def get_services_index(url):
    json_data = requests.get(url).json()
    return json_data
    
with open('gcp_services.json', 'w') as json_file:
        json.dump(get_services_index(url), json_file)

get_data(url, service_url)