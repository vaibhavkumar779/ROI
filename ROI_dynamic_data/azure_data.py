import requests
import json

url = "https://prices.azure.com/api/retail/prices"

def save_data(json_data):
    with open('azure.json', 'w') as json_file:
        json.dump(json_data, json_file)


def get_data(url):
    json_data = requests.get(url).json()
    save_data(json_data)

    if json_data["NextPageLink"]:
        url = json_data["NextPageLink"]
        get_data(url)

get_data(url)