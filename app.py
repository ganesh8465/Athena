import random
import duckdb
import locale
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from Domain import process_data,payment_col,result_table,domain_calculation,User_cost,df_domain
from Hosting import process_data_hosting,payment_col_hosting,result_table_hosting,Hosting_calculation,df_host
from Addon import payment_col_addon,Hostingaddon_calculation,df_addon
from Invoice import invoice_calculation,process_invoice,Duplicate_removal,df_invoice,invoice_table,Duplicate_removal_Rev,revenue
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA



st.set_page_config(page_title="Athena", page_icon=":bar_chart:",layout="wide")


domain_data = None
hosting_data = None
hostingaddon_data = None
invoice_data = None

st.title(" :dart: Athena ")
st.markdown("<h2 style='text-align: left; color: #F5F5F5;'>Easy On Net</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Data Uploader ")
    invoice_file = st.file_uploader("Upload Invoice CSV", type=["csv"])
    domain_file = st.file_uploader("Upload Domain CSV", type=["csv"])
    hosting_file = st.file_uploader("Upload Hosting CSV", type=["csv"])
    hostingaddon_file = st.file_uploader("Upload Hosting Addons CSV", type=["csv"])
    ticket_file = st.file_uploader("Upload Ticket CSV", type=["csv"])

left_column_1, pass_1 ,right_column_1 = st.columns(3)
with left_column_1:
    pass
with pass_1:
    pass
with right_column_1:
    value = st.number_input("Select Cost Per Ticket", value=75.0 ,step=0.01)

custom_css = """
<style>
.card {
  color: #000000;
  background-color: #FFFFF0;
  border: 1px solid #E0E0E0;
  border-radius: 5px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-width: 300px;
  text-align: center;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
 

if domain_file is None and hosting_file is None and hostingaddon_file is None and invoice_file is None:
    st.info("Please upload all files through config", icon="ℹ️")
    st.stop()

@st.cache_data
def load_data(path: str):
    try:
        if path is None:
            raise FileNotFoundError(" Please upload the remaining files.")
        df = pd.read_csv(path)
        return df
    except Exception as e:
        st.error(f"{str(e)}")
        st.stop()

domain_data = load_data(domain_file)
hosting_data = load_data(hosting_file)
hostingaddon_data = load_data(hostingaddon_file)
invoice_data = load_data(invoice_file)
ticket_data = load_data(ticket_file)


cleaned_domain = process_data(domain_data)
domain_df = df_domain(cleaned_domain)
Domain_table = payment_col(cleaned_domain)
Domain_revenue = result_table(Domain_table)
Domain_result = domain_calculation(domain_df)
Domain_cost = User_cost(Domain_result)

cleaned_hosting = process_data_hosting(hosting_data)
data_hosting = df_host(cleaned_hosting)
hosting_result = payment_col(data_hosting)
hosting_revenue = result_table_hosting(hosting_result)
hosting_result = Hosting_calculation(data_hosting)
hosting_cost = User_cost(hosting_result)

cleaned_hostingaddon = process_data_hosting(hostingaddon_data)
data_addon = df_addon(cleaned_hostingaddon)
hostingaddon_result = payment_col(data_addon)
hostingaddon_revenue = result_table_hosting(hostingaddon_result)
hostingaddon_result = Hostingaddon_calculation(data_addon)
hostingaddon_cost = User_cost(hostingaddon_result)

cleaned_invoice = process_invoice(invoice_data)
data_invoice = df_invoice(cleaned_invoice)
invoice_result = invoice_calculation(data_invoice)
invoice = Duplicate_removal(invoice_result)
invoice_df = invoice_table(data_invoice)
invoice_revenue = Duplicate_removal_Rev(invoice_df)

cleaned_ticket = process_invoice(ticket_data)
cleaned_ticket['No of Ticket'] = cleaned_ticket.groupby('userid')['userid'].transform("count")

#cleaned_ticket['date'] = pd.to_datetime(cleaned_ticket['date'], format='%d-%m-%Y')
ticket = pd.DataFrame(data=cleaned_ticket, columns=("userid","No of Ticket"))
ticket = ticket.drop_duplicates(subset='userid', keep='first')
#data = cleaned_ticket.dtypes()


hostingaddon_cost_new = pd.DataFrame(data = hostingaddon_cost, columns=["userid","Final_status","total_free_service_cost","lagging_billing_cycle"])
hosting_cost_new = pd.DataFrame(data = hosting_cost, columns=["userid","Final_status","total_free_service_cost","lagging_billing_cycle"])
Domain_cost_new = pd.DataFrame(data = Domain_cost, columns=["userid","Final_status","total_free_service_cost","lagging_billing_cycle"])
invoice_cost_new = pd.DataFrame(data = invoice, columns=["userid", "12month_revenue","12month_period"])
Domain_cost_new['product'] = 'domain'
hosting_cost_new['product'] = 'hosting'
hostingaddon_cost_new['product'] = 'hostingaddons'
combined_df = pd.concat([Domain_cost_new, hosting_cost_new, hostingaddon_cost_new], ignore_index=True)
summary_data1 = pd.merge(hostingaddon_cost_new, hosting_cost_new, on='userid', how='outer', suffixes=('_addon', '_hosting'))
Domain_cost_new.columns = ['userid', 'Final_status_domain', 'total_free_service_cost_domain',"lagging_billing_cycle_domain","product"]
summary_data2 = pd.merge(summary_data1, Domain_cost_new, on='userid', how='outer', suffixes=('_merged', '_domain'))
summary_data3 = pd.merge(summary_data2, invoice_cost_new, on='userid', how='outer')
summary_data3['free_service_cost_all_products'] = summary_data3.filter(like='total_free_service_cost_').sum(axis=1)


# # # Calculate acquisition cost using the user-provided multiplier

Invoice_Revenue_12months = summary_data3['12month_revenue'].sum()
Free_Service_cost = summary_data3['free_service_cost_all_products'].sum()


data = {
'Metric': ['Annual Revenue', 'Free Service Cost'],
'Value': [Invoice_Revenue_12months, Free_Service_cost]}
ac_df = pd.DataFrame(data)


Domain_revenue['product'] = 'domain'
hosting_revenue['product'] = 'hosting'
hostingaddon_revenue['product'] = 'hostingaddons'
invoice_revenue_new = pd.DataFrame(data = invoice_revenue, columns=["userid", "No of Paid Invoices","Revenue"])
combined_revenue = pd.concat([Domain_revenue, hosting_revenue, hostingaddon_revenue], ignore_index=True)
summary_revenue1 = pd.merge(hostingaddon_revenue, hosting_revenue, on='userid', how='outer', suffixes=('_addon', '_hosting'))
Domain_revenue.columns = ['userid', 'Final_status', 'No of Active Services',"payment","Future Revenue","Revenue","product"]
summary_revenue2 = pd.merge(summary_revenue1, Domain_revenue, on='userid', how='outer', suffixes=('_merged', '_domain'))
summary_revenue3 = pd.merge(summary_revenue2, invoice_revenue_new, on='userid', how='outer')
summary_revenue3['Future Revenue_all_products'] = summary_revenue3.filter(like='Future Revenue').sum(axis=1)
summary_revenue3['Revenue_all_products'] = summary_revenue3.filter(like='Revenue').sum(axis=1)
 


summary_revenue3 = summary_revenue3.fillna(0)

combined_revenue = combined_revenue.fillna(0)

result = revenue(combined_revenue)

Active_Clients = result["No of Active Services"].count()




Revenue_History = pd.merge(invoice_revenue_new, ticket, on='userid', how='outer')
Revenue_History = Revenue_History.fillna(0)
Revenue_History["Cost"] = Revenue_History["No of Ticket"]*value
Revenue_History["Profit"] = Revenue_History["Revenue"]-Revenue_History["Cost"]

status_colors = {'Active': '#ACD690', 'Inactive': '#524F4F'}

bar = combined_revenue.groupby(["product","Final_status"])["Revenue"].sum().reset_index()

Profit = Revenue_History["Profit"].sum()

Revenue_Earned = Revenue_History["Revenue"].sum()
Revenue_Earned = round(Revenue_Earned,0)

st.markdown("""---""")

left_column, middle_column, right_column = st.columns(3)
with left_column:
    formatted_Active = Active_Clients.round(0)
    st.markdown(f'<div class="card">No of Active Clients: <p style="font-size: 24px;">{formatted_Active}</p></div>', unsafe_allow_html=True)
 
with middle_column:
    formatted_revenue = "$ {:,.2f}".format(Revenue_Earned)
    st.markdown(f'<div class="card">Total Revenue Earned: <p style="font-size: 24px;">{formatted_revenue}</p></div>', unsafe_allow_html=True)
 
with right_column:
    formatted_Profit = "$ {:,.2f}".format(Profit)
    st.markdown(f'<div class="card">Profit Earned: <p style="font-size: 24px;">{formatted_Profit}</p></div>', unsafe_allow_html=True)
  

st.markdown("""---""")



fig = px.bar(
    bar,
    x="product",
    y="Revenue",
    color="Final_status",
    color_discrete_map=status_colors,
    text="Revenue",
    barmode='group',
    title="Revenue By Product",
    height=400,
    width=500
)

bar_colors = {'Annual Revenue': '#FFFACD', 'Free Service Cost': '#735E81'}

data1 = px.scatter(summary_revenue3, x = "Future Revenue_all_products", y = "Revenue_all_products", size = "No of Active Services",text="userid")
data1['layout'].update(title="Relationship between Revenue Earned and Future Revenue using Scatter Plot.",
                titlefont = dict(size=20),xaxis = dict(title="Future Revenue",titlefont=dict(size=19),range=[0, 1500]),
                yaxis = dict(title = " Revenue", titlefont = dict(size=19),range=[0, 10000] ),width = 500)
data1.update_traces(marker=dict(color='#BEF574'))

left, right = st.columns(2)
with left:
    st.plotly_chart(fig)
with right:
    st.plotly_chart(data1)


st.subheader("Profit Table")
st.write(Revenue_History)

def table(df):
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df = df[df['status'] == 'Paid']
    for year in range(2010, 2024):
        df[str(year)] = df['date'].dt.year.eq(year) * df['total']
    # Group by 'userid' and aggregate using the sum function
    result = df.groupby('userid', as_index=False).agg(
    {
        '2010': 'sum',
        '2011': 'sum',
        '2012': 'sum',
        '2013': 'sum',
        '2014': 'sum',
        '2015': 'sum',
        '2016': 'sum',
        '2017': 'sum',
        '2018': 'sum',
        '2019': 'sum',
        '2020': 'sum',
        '2021': 'sum',
        '2022': 'sum',
        '2023': 'sum',
        'date': ['min', 'max']
    }
    )
    result.columns = ['userid', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', 'signup_year', 'signoff_year']
    result['signup_year'] = result['signup_year'].dt.strftime('%Y')
    result['signoff_year'] = result['signoff_year'].dt.strftime('%Y')
    return result

df = table(cleaned_invoice)

actual_subscribers = df.iloc[:, 1:-2].apply(lambda x: (x > 0).sum(), axis=0)
additions = df['signup_year'].value_counts().sort_index()
disengagement = df['signoff_year'].value_counts().sort_index()
actual_revenue = df.iloc[:, 1:-2].sum()
ARPU = actual_revenue/actual_subscribers
 
 
sbc = pd.DataFrame({'actual_subscribers': actual_subscribers,
                    'additions': additions,
                    'disengagement': disengagement,
                    'actual_revenue': actual_revenue,
                    'ARPU': ARPU,
                    }).T
sbc = sbc.round(2)
 
growth_rate = sbc.loc['additions'] / sbc.loc['actual_subscribers'].shift(1, fill_value=0)
#growth_rate = growth_rate.apply(lambda x: f"{x:.2%}")
churn_rate = sbc.loc['disengagement'] / sbc.loc['actual_subscribers'].shift(1, fill_value=0)
#churn_rate = churn_rate.apply(lambda x: f"{x:.2%}")
forecast_subscribers = sbc.loc['actual_subscribers'].shift(1, fill_value=0) - sbc.loc['actual_subscribers'].shift(1, fill_value=0) * churn_rate.shift(1, fill_value=0) + sbc.loc['actual_subscribers'].shift(1, fill_value=0) * growth_rate.shift(1, fill_value=0)
forecast_revenue = sbc.loc['ARPU'].shift(1,fill_value=0) * forecast_subscribers
diff = forecast_revenue - sbc.loc['actual_revenue']
diffff = ((diff/sbc.loc['actual_revenue'])*100)
 
bc = pd.DataFrame({
    'Growth rate': growth_rate,
    'churn rate': churn_rate,
    'Forecast subscribers': forecast_subscribers,
    'Forecast revenue': forecast_revenue,
    'Variance': diff,
    'var_rate': diffff
}).T

bc = bc.round(2)

def color_styling(val, col_name):
    if col_name == 'Growth rate':
        color = 'red' if val < 0.1 else 'green'  # Assuming 10% is the threshold
        return f'color: {color}; font-weight: bold;' + (f'content: "{val:.2%}";' if isinstance(val, float) else '')
    elif col_name == 'churn rate':
        color = 'green' if val < 0.05 else 'red'
        return f'color: {color}; font-weight: bold;' + (f'content: "{val:.2%}";' if isinstance(val, float) else '')
    else:
        return 'color: black'

forecast_table = pd.concat([sbc, bc], axis=0)

# Function to format numbers with commas and two decimal places
def format_numbers(val):
    if isinstance(val, (int, float)):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # Set locale to US for comma separators
        return locale.format_string("%.2f", val, grouping=True)  # Format with two decimal places and commas for thousands
    return val

# Apply the combined styling function to the DataFrame
styled_table_1 = forecast_table.style.applymap(lambda val: color_styling(val, 'Growth rate'), subset=pd.IndexSlice[['Growth rate'], :])
styled_table_1 = styled_table_1.applymap(lambda val: color_styling(val, 'churn rate'), subset=pd.IndexSlice[['churn rate'], :])

# Apply formatting to numerical columns
format_dict = {col: format_numbers for col in bc.columns if bc[col].dtype in ['float64', 'int64']}
styled_table_1 = styled_table_1.format(format_dict)

# # Display the styled table using Streamlit write() method with Markdown
# st.subheader("Revenue Forecast")
# st.markdown(styled_table_1.render(), unsafe_allow_html=True)
# st.text("")

required_rows = ['Growth rate', 'churn rate', 'actual_revenue']
extracted_df = forecast_table.T.reset_index()
extracted_df = extracted_df.rename(columns={'index': 'Year'})

st.markdown("""---""")    

st.subheader("Acquisition Calculator")

st.markdown("""---""")

left_C,middle_C,right_C= st.columns(3)
with left_C:
    selected_value = st.slider("Select Acquisition multiplier", min_value=1.0, max_value=3.0, step=0.1)
with middle_C:
    op_cost = st.number_input("Provide operational cost ", value=1)
with right_C:
    ac_df_1 = ac_df.T.reset_index()
    ac_df_1.columns = ac_df_1.iloc[0]  # Set the first row as column names
    ac_df_1 = ac_df_1[1:]  # Exclude the first row
    
    # Assuming you want to subtract Free Service Cost and op_cost from Annual Revenue
    ac_df_1['acquisition_cost'] = (ac_df_1['Annual Revenue'] - ac_df_1['Free Service Cost'] - op_cost) * selected_value
    acquisition_cost = ac_df_1['acquisition_cost'].astype(float).round(2)
    formatted_acquisition = "$ {:,.2f}".format(acquisition_cost.iloc[0])

    st.markdown(f'<div class="card">Total Acquisition Cost: <p style="font-size: 24px;">{formatted_acquisition}</p></div>', unsafe_allow_html=True)
st.markdown("""---""")    

fig2= px.bar(
    ac_df,
    x="Metric",
    y="Value",
    title="Annual Revenue Vs Cost",
    height=400,
    width=500,
    color='Metric',
    color_discrete_map=bar_colors
)
# Add data labels using the 'text' property
fig2.update_traces(textposition='inside', texttemplate='%{y:.2f}', selector=dict(type='bar'))

fig2.update_layout(bargap=0.2) 

st.plotly_chart(fig2)




st.markdown("""---""")

st.subheader("Revenue Projection Analysis and Model Comparison")
st.markdown("""---""")
st.write("<p style='font-size:20px'><strong>Revenue Forecast using Data Science Model</strong></p>",unsafe_allow_html=True)
# Data preprocessing
extracted_df['Year'] = pd.to_datetime(extracted_df['Year'], format='%Y')
extracted_df.set_index('Year', inplace=True)

# Exclude actual values in 2023
actual_revenue_2023 = extracted_df.loc['2023-01-01':'2023-12-31', 'actual_revenue']
extracted_df = extracted_df.drop(actual_revenue_2023.index)

# Model training
model = sm.tsa.ExponentialSmoothing(extracted_df['actual_revenue'], trend='add', seasonal='add', seasonal_periods=2)
fit = model.fit()

# Forecasting next 3 years
forecast = fit.forecast(steps=3)

# Create a figure for visualization
fig_1, ax = plt.subplots(figsize=(12, 6))
ax.plot(extracted_df['actual_revenue'], label='Actual Revenue')
ax.plot(fit.fittedvalues, label='Fitted Values', linestyle='--')
ax.plot(fit.forecast(steps=3), label='Forecasted Revenue', linestyle='--')
ax.set_title('Revenue Forecast')
ax.set_xlabel('Year')
ax.set_ylabel('Revenue')
ax.legend()


# Display the plot in Streamlit
st.pyplot(fig_1)

# Display the forecasted revenue

formatted_forecast = forecast.round(2).apply(lambda x: f"${x:,.2f}")

st.write(formatted_forecast)


# Display the styled table using Streamlit write() method with Markdown
with st.expander("**Historical Performance and Forecast Analysis**"):
    st.write(styled_table_1)

st.write("<p style='font-size:20px'><strong>Revenue Forecast with Linear Growth Rate Model</strong></p>", unsafe_allow_html=True)

left_R,right_R= st.columns(2)
with left_R:
    # Calculate average growth rate
    average_growth_rate = 0.1
    # Display the average growth rate as a number input
    new_growth_rate = st.number_input('Enter new growth rate:', value=average_growth_rate)
    # Update the average_growth_rate if the user inputs a new value
    if new_growth_rate != average_growth_rate:
        average_growth_rate = new_growth_rate
with right_R:
    # Set churn rate to be less than 5%
    churn_rate_forecast = 0.05  # Your churn rate logic here, considering the historical data
    new_churn_rate = st.number_input('Enter new churn rate:', value=churn_rate_forecast)
    # Update the churn rate if the user inputs a new value
    if new_churn_rate != churn_rate_forecast:
        churn_rate_forecast = new_churn_rate

adjusted_growth_rate = average_growth_rate - churn_rate_forecast

# Forecasting for 2024 and 2025 with calculated growth and churn rates
forecast_2024 = (forecast[0] * (1 + adjusted_growth_rate)).astype(int)
forecast_2025 = (forecast_2024 * (1 + adjusted_growth_rate)).astype(int)  # Assuming a linear growth pattern
forecast_2026 = (forecast_2025 * (1 + adjusted_growth_rate)).astype(int) 


formatted_forecast_2024 = "$ {:,.2f}".format(forecast_2024)
formatted_forecast_2025 = "$ {:,.2f}".format(forecast_2025)
formatted_forecast_2026 = "$ {:,.2f}".format(forecast_2026)
st.write("Forecasted Revenue for 2024: ", formatted_forecast_2024)
st.write("Forecasted Revenue for 2025: ", formatted_forecast_2025)
st.write("Forecasted Revenue for 2026: ", formatted_forecast_2026)