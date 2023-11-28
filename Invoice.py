import pandas as pd
from datetime import datetime, timedelta

def df_invoice(data):
    data = pd.DataFrame(data,columns=("userid", "date","status","total"))
    return data

def invoice_calculation(data):
    data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
    twelve_months_ago = datetime.now() - timedelta(days=365)
    data['12month_period'] = (data["date"] >= twelve_months_ago) & (data["date"]  <= datetime.now() - timedelta(days=1)) & (data["date"].notna())
    data['12month_revenue'] = data[(data['12month_period']) & (data['status'] == 'Paid')].groupby('userid')['total'].transform('sum')  
    data = data.reset_index()
    return data


def invoice_table(data):
    data['No of Paid Invoices'] = data[(data['status'] == 'Paid') & (data['total'] > 0) ].groupby('userid')['userid'].transform('count')
    data['Revenue'] = data[(data['status'] == 'Paid')].groupby('userid')['total'].transform('sum')
    return data

def process_invoice(data):
    ##data = pd.read_csv(file_upload)

    # Remove rows with missing values in the "id" column
    data = data.dropna(subset=["id"])

    # Convert the "id" column to numeric, non-numeric values become NaN
    data["id"] = pd.to_numeric(data["id"], errors="coerce")

    # Remove rows with NaN values in the "id" column
    data = data.dropna(subset=["id"])

    # Remove rows with missing values in the "userid" column
    data = data.dropna(subset=["userid"])

    # Convert the "userid" column to numeric, non-numeric values become NaN
    data["userid"] = pd.to_numeric(data["userid"], errors="coerce")

    # Remove rows with NaN values in the "userid" column
    data = data.dropna(subset=["userid"])

    # Remove rows with '0' values in "userid" column
    data = data[data['userid'] != 0]

    return data

def Duplicate_removal(data):
    data = data.sort_values(by=['userid','12month_revenue'], ascending=[True,False])
    data = data.drop_duplicates(subset='userid', keep='first')

    return data

def Duplicate_removal_Rev(data):
    data = data.sort_values(by=['userid','No of Paid Invoices'], ascending=[True,False])
    data = data.drop_duplicates(subset='userid', keep='first')

    return data

def highest_revenue_product(series):
    return series.loc[series.idxmax()]
# Define a custom aggregation function for the "Final_status" column
def active_status(series):
    return 'Active' if 'Active' in series.values else 'Inactive'

def revenue(data):
    # Group the data by "userid"
    grouped = data.groupby('userid')
    # Define a custom aggregation function for the "product" column
    aggregations = {
        'No of Active Services': 'sum',
        'payment': 'sum',
        'Future Revenue': 'sum',
        'Revenue': 'sum',
        }
    # Apply the aggregations
    result = grouped.agg(aggregations).reset_index()

    return result