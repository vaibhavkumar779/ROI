# Flask Setup
from flask import Flask, request, render_template
import spreadsheet
import pandas as pd

app = Flask(__name__, template_folder='./templates')

roi_sheet = spreadsheet.sheet_init()
row = 2

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html', title="Home Page")

@app.route('/index', methods = ['GET','POST'])
def costdata():
    if request.method == 'POST':
        global row
        User = request.form['User']
        RAM = float(request.form['RAM'])
        vCPUs = int(request.form['vCPUs'])
        OS = request.form['OS']
        NodeStorage= int(request.form['NodeStorage'])
        Cloud = request.form['Cloud']
        Number_of_Nodes = int(request.form['No of nodes'])
        
        if request.form.get('submit_button') == 'submit':
            # send data to gsheet
            data = [User,RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes]
            UserSheet = roi_sheet.worksheet('Dashboard 1')
            UserSheet.insert_row(data,row)
            row = row + 1

            if Cloud == "AWS":
                node_cost = spreadsheet.aws_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)
            elif Cloud == "GCP":
                node_cost = spreadsheet.gcp_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)
            else:
                node_cost = spreadsheet.azure_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)

            node_cost.index.name=None
            return render_template('index.html',title="Dashboard",tables=[node_cost.head().to_html(index = False)],titles = ['Cloud Cost for nearest Node Config'],Heading="{} Node Data".format(Cloud))

        elif request.form.get('submit_button')=="compare":
            aws_node_cost = spreadsheet.aws_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)
            gcp_node_cost = spreadsheet.gcp_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)
            azure_node_cost = spreadsheet.azure_cost(RAM,vCPUs,OS,NodeStorage,Cloud,Number_of_Nodes)
            combine_cost = spreadsheet.cost_data_combine(aws_node_cost,gcp_node_cost,azure_node_cost)

            labels= combine_cost['Machine or Service'].values.tolist()
            values= combine_cost['monthly cost'].values.tolist()

            return render_template('index.html',title="Dashboard",labels=labels,values=values,\
                tables=[aws_node_cost.head(2).to_html(index = False),gcp_node_cost.head(2).to_html(index = False),azure_node_cost.head(2).to_html(index = False)],titles = ['Ae','AWS','GCP Node','Azure Node'],Heading="Compare Data")
    elif request.method == 'GET':
        return render_template('index.html', title="Dashboard")

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0",port=9999)