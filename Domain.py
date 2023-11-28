import pandas as pd
from datetime import datetime, timedelta



def df_domain(data):
    data = pd.DataFrame(data,columns=("userid", "nextinvoicedate","Final_status","firstpaymentamount","recurringamount"))
    return data

def process_data(data):
    data = data.dropna(subset=["id"])
    data["id"] = pd.to_numeric(data["id"], errors="coerce")
    data = data.dropna(subset=["id"])
    data = data.dropna(subset=["userid"])
    data["userid"] = pd.to_numeric(data["userid"], errors="coerce")
    data = data.dropna(subset=["userid"])
    data = data[data['userid'] != 0]
    def get_status_domain(row):
        if pd.isna(row['nextinvoicedate']):
            return 'Inactive'
        next_invoice_date = datetime.strptime(row['nextinvoicedate'], '%Y-%m-%d')
        today = datetime.now()
        ninety_days_ago = today - timedelta(days=90)
        if next_invoice_date >= ninety_days_ago:
            return 'Active'
        else:
            return 'Inactive'
    
    data['Final_status'] = data.apply(get_status_domain, axis=1)
    return data

# Define a function to calculate the 'payment' based on the conditions
def calculate_payment(row):
    if row['nextinvoicedate'] == row['min_nextinvoicedate']:
        return row['firstpaymentamount']
    else:
        return row['recurringamount']

    
def payment_col(data):
    data['nextinvoicedate'] = pd.to_datetime(data['nextinvoicedate'], format='%Y-%m-%d')
    data['min_nextinvoicedate'] = data.groupby('userid')['nextinvoicedate'].transform('min')
    data['payment'] = data.apply(calculate_payment, axis=1)
    return data



def result_table(data):
    data['No of Active Services'] = data[(data['payment'] > 0) & (data['Final_status'] == 'Active')].groupby('userid')['userid'].transform('count')
    today = datetime.now()
    data['Future Revenue'] = data[(data['nextinvoicedate'] > today) & (data['Final_status'] == 'Active')].groupby('userid')['payment'].transform('sum')
    data['Revenue'] = data[(data['payment'] > 0) & (data['status'] == 'Active')].groupby('userid')['payment'].transform('sum')
    data = data.reset_index()
    data = data.sort_values(by=['userid','Final_status'], ascending=[True,True])
    #data = data.drop_duplicates(subset='userid', keep='first')
    data = pd.DataFrame(data, columns=("userid",'Final_status','payment','No of Active Services','Future Revenue','Revenue'))
    result = data.groupby('userid').agg({'Final_status': lambda x: 'Active' if 'Active' in x.values else x.values[0],
    'No of Active Services': 'max',
    'payment':'max',
    'Future Revenue': 'max',
    'Revenue': 'max'}).reset_index()
    return result

def calculate_lagging_billing_cycle(row):
    if row['Final_status'] == "Inactive":
        return 0
    elif row['Final_status'] == "Active":
        next_invoice_date = pd.to_datetime(row['nextinvoicedate'], format='%Y-%m-%d')
        today = pd.Timestamp.now()
        return (next_invoice_date - today).days / 30

    

def domain_calculation(data):

    data['lagging_billing_cycle'] = data.apply(calculate_lagging_billing_cycle, axis=1)
    
    data['1month_revenue'] = data['recurringamount'] / 12

    data['freeserviceperiodflag'] = data['lagging_billing_cycle'].apply(lambda x: 'True' if x > 0 else 'False')

    data['free_service_period_cost'] = data.apply(lambda row: row['lagging_billing_cycle'] * row['1month_revenue'] if row['freeserviceperiodflag'] == 'True' else 0, axis=1)

    return data

def User_cost(data):
    
    data['total_free_service_cost'] = data.groupby('userid')['free_service_period_cost'].transform('sum')
    data = data.sort_values(by=['Final_status'], ascending=[True])
    data = data.drop_duplicates(subset='userid', keep='first')
    data = data.reset_index()
    return data



    