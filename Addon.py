import pandas as pd
from datetime import datetime, timedelta
from Hosting import calculate_lagging_billing_cycle_Host

def df_addon(data):
    data = pd.DataFrame(data, columns=("userid","firstpaymentamount","recurring","status","billingcycle","nextinvoicedate","Final_status"))
    column_mapping = {"recurring":"recurringamount"}
    data = data.rename(columns=column_mapping)
    return data

def calculate_payment(row):
    if row['nextinvoicedate'] == row['min_nextinvoicedate']:
        return row['firstpaymentamount']
    else:
        return row['recurring']

    
def payment_col_addon(data):
    data['nextinvoicedate'] = pd.to_datetime(data['nextinvoicedate'], format='%Y-%m-%d')
    data['min_nextinvoicedate'] = data.groupby('userid')['nextinvoicedate'].transform('min')
    data['payment'] = data.apply(calculate_payment, axis=1)
    return data

def calculate_1month_revenue_hostingaddon(row):
    if row['freeserviceperiodflag'] == 'True':
        if row['billingcycle'] == 'Annually':
            return row['recurringamount'] / 365
        elif row['billingcycle'] == 'Monthly':
            return row['recurringamount'] / 30
        elif row['billingcycle'] == 'Biennially':
            return row['recurringamount'] / 730
        elif row['billingcycle'] == 'Semi-Annually':
            return row['recurringamount'] / 182.5
        elif row['billingcycle'] == 'Triennially':
            return row['recurringamount'] / 1095
        elif row['billingcycle'] == 'Quarterly':
            return row['recurringamount'] / 91.25
    else:
        return 0

def Hostingaddon_calculation(data):

    data['lagging_billing_cycle'] = data.apply(calculate_lagging_billing_cycle_Host, axis=1)

    data['freeserviceperiodflag'] = data['lagging_billing_cycle'].apply(lambda x: 'True' if x > 0 else 'False')
    
    data['1month_revenue'] = data.apply(calculate_1month_revenue_hostingaddon, axis=1)

    data['free_service_period_cost'] = data.apply(lambda row: row['lagging_billing_cycle'] * row['1month_revenue'] if row['freeserviceperiodflag'] == 'True' else 0, axis=1)


    return data