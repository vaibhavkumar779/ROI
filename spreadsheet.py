# Google Sheets API Setup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO


def sheet_init():
    path_to_creds = "credentials.json"
    credential = ServiceAccountCredentials.from_json_keyfile_name(path_to_creds,
                                                                  ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                                                                   "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(credential)
    roi_sheet = client.open_by_url(
        'https://docs.google.com/spreadsheets/d/1cttsFZTevLF1CC6suvEoHdMAyCPFwe23qCV1Smvx7BI')

    return roi_sheet


def aws_cost(RAM, vCPUs, OS, StorageUnitSize, Cloud, Number_of_Nodes, StorageType, Number_of_Storage_Units):

    aws_data = get_data("AWS")
    # AWS cost logic
    # Node data
    aws_node = aws_data[aws_data['Resource Type'] == 'Node']
    # vCPU and RAM
    aws_node = aws_node[(aws_node['vCPUs'] >= vCPUs) & (
        aws_node['RAM'] >= RAM) & (aws_data['OS'] == OS)]
    aws_node = aws_node.drop(columns=[
                             'Resource Type', 'monthly', 'Storage count', 'Resource', 'Storage type', 'Network performance'])

    # taking 730 hours for month
    aws_node['monthly cost node'] = [
        value * Number_of_Nodes * 730 for value in aws_node['hourly']]
    aws_node_cost = aws_node

    # Storage data
    aws_store = aws_data[aws_data["Resource Type"] == 'Storage']
    if StorageType == "Magnetic":
        aws_store = aws_store[~ aws_store["Machine or Service"].str.contains(
            StorageType)]
    else:
        aws_store = aws_store[aws_store["Machine or Service"].str.contains(
            StorageType)]
    aws_store['Number of Units'] = Number_of_Storage_Units
    aws_store['Overall Storage cost'] = aws_store['monthly'] * \
        StorageUnitSize * Number_of_Storage_Units
    aws_store_cost = aws_store.drop(
        columns=['vCPUs', 'RAM', 'Network performance', 'OS'])

    return aws_node_cost, aws_store_cost


def gcp_cost(RAM, vCPUs, OS, StorageUnitSize, Cloud, Number_of_Nodes, StorageType, Number_of_Storage_Units):

    gcp_data = get_data("GCP")
    # GCP cost logic
    # Node data
    gcp_node = gcp_data[gcp_data['Resource Type'] == 'Node']
    gcp_node = gcp_node[(gcp_node['vCPUs'] >= vCPUs)
                        & (gcp_node['RAM'] >= RAM)]
    gcp_node = gcp_node.drop(
        columns=['Resource Type', 'monthly', 'hourly (Spot VM)', 'monthly (Spot VM)'])
    gcp_node['monthly cost node'] = [
        value * Number_of_Nodes * 730 for value in gcp_node['hourly']]
    gcp_node_cost = gcp_node

    # Storage data
    gcp_store = gcp_data[gcp_data["Resource Type"] == 'Storage']
    gcp_store['Number of Units'] = Number_of_Storage_Units
    gcp_store['Overall Storage cost'] = gcp_store['hourly (Spot VM)'] * \
        StorageUnitSize * Number_of_Storage_Units
    gcp_store_cost = gcp_store.drop(
        columns=['vCPUs', 'RAM', 'hourly', 'monthly', 'monthly (Spot VM)'])

    return gcp_node_cost, gcp_store_cost


def azure_cost(RAM, vCPUs, OS, StorageUnitSize, Cloud, Number_of_Nodes, StorageType, Number_of_Storage_Units):

    azure_data = get_data("Azure")
    # Azure Cost Logic
    # Node data
    azure_node = azure_data[(azure_data['Resource Type'] == 'Node')]
    azure_node = azure_node[(azure_node['vCPUs'] > vCPUs) & (
        azure_node['RAM'] >= RAM) & (azure_node['Storage'] >= StorageUnitSize)]
    azure_node = azure_node.drop(columns=['Resource Type', 'monthly', '1 year reserved hourly',
                                 '1 year reserved monthly', '3 year reserved hourly', '3 year reserved monthly'])
    # cost data
    # taking 730 hours for month
    azure_node['monthly cost node'] = [
        value * Number_of_Nodes * 730 for value in azure_node['hourly']]
    azure_node_cost = azure_node

    return azure_node_cost


def get_data(cloud):
    roi_sheet = sheet_init()
    # azure data extraction
    cloud_resource = roi_sheet.worksheet('{} Pricing'.format(cloud))
    # get_all_values gives a list of rows.
    cloud_rows = cloud_resource.get_all_values()
    # creating datframe
    cloud_data = pd.DataFrame.from_records(cloud_rows)
    # reseting the headers  for azure
    cloud_data.columns = cloud_data.iloc[0]
    cloud_data = cloud_data.iloc[1:].reset_index(drop=True)
    cloud_data = cloud_data.apply(pd.to_numeric, errors='ignore').fillna(0)

    return cloud_data


def cost_data_combine(aws_node_cost, gcp_node_cost, azure_node_cost, gcp_store_cost, aws_store_cost, StorageType, Number_of_Storage_Units):

    aws_node_cost['Cloud'] = 'AWS'
    gcp_node_cost['Cloud'] = 'GCP'
    azure_node_cost['Cloud'] = 'Azure'

    # Storage cost addition gcp
    aws_storage_cost = aws_store_cost['Overall Storage cost'].values.tolist()
    aws_storage_name = aws_store_cost['Machine or Service'].values.tolist()
    for i in range(len(aws_storage_cost)):
        aws_node_cost["Storage type"] = aws_storage_name[i]
        aws_node_cost["Cost with Storage"] = aws_node_cost['monthly cost node'] + \
            aws_storage_cost[i]
        

    # Storage cost addition gcp
    gcp_storage_cost = gcp_store_cost['Overall Storage cost'].values.tolist()
    gcp_storage_name = gcp_store_cost['Machine or Service'].values.tolist()
    for i in range(len(gcp_storage_cost)):
        gcp_node_cost["Storage type"] = gcp_storage_name[i]
        gcp_node_cost["Cost with Storage"] = gcp_node_cost['monthly cost node'] + \
            gcp_storage_cost[i]
        

    azure_node_cost['Cost with Storage'] = azure_node_cost['monthly cost node']

    # sorting
    gcp_cost = gcp_node_cost.sort_values(by = ['Cost with Storage'])
    aws_cost = aws_node_cost.sort_values(['Cost with Storage'])
    azure_cost = azure_node_cost.sort_values(by=['Cost with Storage'])
    # comining cost
    combine_node_cost = pd.concat(
        [aws_cost.head(2), gcp_cost.head(2), azure_cost.head(2)], join='outer', axis=0).fillna(0)
    combine_node_cost.reset_index(drop=True, inplace=True)  # index reset

    return combine_node_cost
