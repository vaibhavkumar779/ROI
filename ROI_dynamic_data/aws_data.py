import requests
import json

url = "https://pricing.us-east-1.amazonaws.com"

def save_data(json_data, service_name):
    with open('./AWS_DATA/{} Data.json'.format(service_name), 'w') as json_file:
        json.dump(json_data, json_file)


def get_data(url):
    service_data = get_services_index(url)
    services = service_data["offers"] #this gives the dictionary of services

    for service in services.values():
        service_url = url + service["currentVersionUrl"]
        json_data = requests.get(service_url).json()
        save_data(json_data,service["offerCode"])

    if json_data["NextPageLink"]:
        url = json_data["NextPageLink"]
        get_data(url)

def get_services_index(url):
    url = url + "/offers/v1.0/aws/index.json"
    json_data = requests.get(url).json()
    return json_data
    
with open('aws_services.json', 'w') as json_file:
        json.dump(get_services_index(url), json_file)

get_data(url)