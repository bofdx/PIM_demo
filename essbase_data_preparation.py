import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import gc
import os
from scipy.optimize import newton
from io import StringIO
import matplotlib.pyplot as plt
import plotly.express as px



##########################INPUTS###################################################################################################################################################
col1, col2, col3, col4 =st.columns(4)

with col1:
    reference_year = st.number_input("Reference Year", value=2025, step=1, format="%d")
with col2:
    mid_year_discounting = st.selectbox("Discounting Type", ["Mid-Year", "End of Year"], index=0)
with col3:
    discount_rate = (st.number_input("Discount Rate (%) ", value=10, step=1, format="%d"))/100
with col4:
    inflation_rate = st.number_input("Inflation Rate (%)", value=2.2, step=0.1, format="%.2f") / 100


############################### SET UP CUBE DATA ###################################################################################################################
# Specify the file paths
CP_Path = "Dummy_Data.csv"
CP_Accounts = 'Dim_Account_SPMFS.csv'
#CP_Assets = 'Dim_Asset_CP.txt'

# Load the CP CubeStringIO
df_CP = pd.read_csv(CP_Path, delimiter=',')

# Add in the Account Names -- NOT REQUIRED JUST YET
df_CP_Accounts = pd.read_csv(CP_Accounts, delimiter=',')
df_CP = df_CP.merge(df_CP_Accounts, on='Account')

# df_CP_Assets=pd.read_csv(CP_Assets, delimiter=',')
# df_CP_Assets = df_CP_Assets.rename(columns={df_CP_Assets.columns[1]: 'Asset',df_CP_Assets.columns[3]: 'Asset_Alias'})[['Asset', 'Asset_Alias']]
# df_CP = df_CP.merge(df_CP_Assets, on='Asset')

# df_CP = df_CP.drop(columns=['Year_NA', 'CY2022', 'CY2023', 'Asset'])
# df_CP = df_CP.rename(columns={'Source': 'Case', 'Alias': 'Account','Account':'Alias', 'Asset_Alias': 'Asset'})
# df_CP['Category'] = df_CP['Category'].replace('CAT_Default', 'Default')

#Remove redundant rows and columns
if 'Year_NA' in df_CP.columns:
    df_CP = df_CP.drop(columns=['Year_NA'])
  
df_CP = df_CP[df_CP['Category'] != 'Category']

df_CP['Period']='MTD'

# Specify the columns to retain during the pivot (non-year columns)
id_vars = ['Scenario', 'Version', 'Case', 'Asset', 'Category','Period', 'Unit', 'Basis', 'Account', 'Alias']

# Identify the year columns (those starting with 'CY')
year_columns = [col for col in df_CP.columns if col.startswith('CY')]

# Melt the DataFrame to make 'Year' a column and the cash flows as values
df_essbase = df_CP.melt(id_vars=id_vars, value_vars=year_columns, 
                             var_name='Year', value_name='Value')

# Remove 'CY' from the 'Year' column and convert to integer
df_essbase['Year'] = df_essbase['Year'].str.replace('CY', '').astype(int)

################### Add in Discount Factors #######################################################################################################################

if mid_year_discounting == "Mid-Year":
    # Calculate Discount_Factor using mid-year discounting
    df_essbase['Discount_Factor'] = 1 / ((1 + discount_rate) ** (df_essbase['Year'] - reference_year + 0.5))
    df_essbase['Real_Discount_Factor'] = 1/((1+inflation_rate)**(df_essbase['Year'] - reference_year + 0.5))
else:
    df_essbase['Discount_Factor'] = 1 / ((1 + discount_rate) ** (df_essbase['Year'] - reference_year))
    df_essbase['Real_Discount_Factor'] = 1/((1+inflation_rate)**(df_essbase['Year'] - reference_year))

################### SECTION TO SUM TOCS -TO BE ADDED ##############################################################################################################

################### SECTION TO CALCULATE INCREMENTALS TO BE ADDED #################################################################################################
st.write(df_essbase)



#####################################################################################################################################################################
################ This section will eventually be split out on its own##############################################################################################
#####################################################################################################################################################################

######## NPV10, IRR, Total ATCF CALCULATION #################################################################################################################################################################################################################################################################

# Filter the DataFrame for the 'ATCF_TOC' Account and make a copy
df_atcf = df_essbase[df_essbase['Account'] == 'OA0008'].copy()

# Calculate Present Value for each row
df_atcf.loc[:, 'Present_Value'] = df_atcf['Value'] * df_atcf['Discount_Factor']


# Group by 'Scenario', 'Asset', and 'Case' and sum the 'Present_Value'
npv_summary = df_atcf.groupby(['Scenario','Version', 'Asset', 'Case'])['Present_Value'].sum().reset_index()
npv_summary = npv_summary.rename(columns={'Present_Value': 'NPV10 (USDM)'})

# Sum the 'Value' column (Total ATCF US$M Nominal)
total_atcf_summary = df_atcf.groupby(['Scenario','Version', 'Asset', 'Case'])['Value'].sum().reset_index()
total_atcf_summary = total_atcf_summary.rename(columns={'Value': 'Total ATCF US$M Nominal'})

# Calculate IRR for each group using Newton's method (same as excel)

def calculate_irr(cash_flows):
    # Ensure cash flows are a NumPy array
    cash_flows = np.array(cash_flows)

    # Define the NPV function as a lambda for IRR calculation
    def npv(rate):
        return np.sum(cash_flows / (1 + rate) ** np.arange(len(cash_flows)))

    # Handle cases where IRR might fail:
    # - Ensure there's at least one positive and one negative cash flow
    if (cash_flows > 0).any() and (cash_flows < 0).any():
        try:
            # Use Newton's method with a reasonable starting guess (e.g., 10% or 0.1)
            irr = newton(npv, x0=0.1)
            return irr * 100  # Convert to percentage
        except RuntimeError:
            # Newton's method failed to converge
            return np.nan
    else:
        # If all cash flows are the same sign, IRR is undefined
        return np.nan

# Calculate IRR for each group and replace NaNs with 0
irr_summary = df_atcf.groupby(['Scenario','Version', 'Asset', 'Case'])['Value'].apply(
    lambda x: calculate_irr(x.fillna(0).values)
).reset_index()

irr_summary = irr_summary.rename(columns={'Value': 'IRR (%)'})

# Merge the NPV, IRR, and Total ATCF summaries
overall_summary = pd.merge(npv_summary, irr_summary, on=['Scenario','Version', 'Asset', 'Case'], how='left')
overall_summary = pd.merge(overall_summary, total_atcf_summary, on=['Scenario','Version', 'Asset', 'Case'], how='left')

# Convert IRR to a percentage format
overall_summary['IRR (%)'] = (overall_summary['IRR (%)'] ).round(2)


######## PRODUCTION CALCULATIONS ###############################################################################################################################################################################################################################################################################

# Filter the DataFrame for the production volume in BOE Account and make a copy
df_prod = df_essbase[df_essbase['Account'] == 'PV'].copy()

# Calculate Present Value for each row using .loc to avoid the warning
df_prod.loc[:, 'Present_Value'] = df_prod['Value'] * df_prod['Discount_Factor']

# Calculate discounted production and total production
prod_summary = (
    df_prod.groupby(['Scenario','Version', 'Asset', 'Case'])
    .agg(
        Discounted_Production_mmbbl=('Present_Value', 'sum'),
        Total_Production_mmboe=('Value', 'sum'),
    )
    .reset_index()
)

# Find the peak Total Production for each combination
peak_production = (
    df_prod.groupby(['Version', 'Scenario', 'Asset', 'Case'])['Value']
    .max()
    .reset_index()
    .rename(columns={'Value': 'Peak_Total_Production_mmboe'})
)

# Merge the peak production data into the production summary table
prod_summary = pd.merge(prod_summary, peak_production, on=['Version', 'Scenario', 'Asset', 'Case'],how='left')

# Filter rows with non-zero production to find the first non-zero production year
non_zero_prod = df_prod[df_prod['Value'] > 0]
first_non_zero_year = (
    non_zero_prod.groupby(['Scenario','Version', 'Asset', 'Case'])['Year']
    .min()
    .reset_index()
    .rename(columns={'Year': 'RFSU (First non-zero production year)'})
)

# Merge the first non-zero production year into the summary
prod_summary = pd.merge(prod_summary, first_non_zero_year, on=['Scenario','Version', 'Asset', 'Case'], how='left')

# Add the first non-zero production year to the main production DataFrame
df_prod = pd.merge(
    df_prod, 
    first_non_zero_year, 
    on=['Scenario','Version', 'Asset', 'Case'], 
    how='left'
)

# Calculate years online and filter for the first five years
df_prod['Years Online'] = df_prod['Year'] - df_prod['RFSU (First non-zero production year)'] + 1
df_first_five_years = df_prod[(df_prod['Years Online'] >= 1) & (df_prod['Years Online'] <= 5)]


# Calculate the average production for the first five years
avg_production = (
    df_first_five_years.groupby(['Scenario','Version', 'Asset', 'Case'])['Value']
    .mean()
    .reset_index()
    .rename(columns={'Value': 'Avg Production (First 5 Years)'})
)

# Merge the 5yr average production into the summary
prod_summary = pd.merge(
    prod_summary, 
    avg_production, 
    on=['Scenario','Version', 'Asset', 'Case'], 
    how='left')

# Merge the prod_summary into the overall summary
overall_summary = pd.merge(
    overall_summary, 
    prod_summary, 
    on=['Version','Scenario', 'Asset', 'Case'], 
    how='left')


############### Total Real CAPEX, Total Discounted CAPEX & Real CAPEX to RFSU ######################################################################################################################################################################################################################################################################

# Filter the DataFrame to total capex
df_capex = df_essbase[(df_essbase['Account'] == 'CX') & (df_essbase['Category'] == 'CAT_CAPEX')].copy()


# Calculate real capex for each row using .loc to avoid the warning
df_capex.loc[:, 'CAPEX_real'] = -df_capex['Value'] * df_capex['Real_Discount_Factor']

# Group by 'Scenario', 'Asset', and 'Case' and sum the 'real capex'
capex_summary = df_capex.groupby(['Scenario', 'Version','Asset', 'Case'])['CAPEX_real'].sum().reset_index()
capex_summary = capex_summary.rename(columns={'CAPEX_real':'Total CAPEX (US$M Real)'})

# Merge the capex_summary into the overall summary
overall_summary = pd.merge(
    overall_summary, 
    capex_summary, 
    on=['Scenario', 'Version','Asset', 'Case'], 
    how='left')


# Calculate discounted capex (i=10%) for each row using .loc to avoid the warning
df_capex.loc[:, 'CAPEX_discounted'] = -df_capex['Value'] * df_capex['Discount_Factor']


# Group by 'Scenario', 'Asset', and 'Case' and sum the 'discounted capex'
capex_disc_summary = df_capex.groupby(['Scenario', 'Version','Asset', 'Case'])['CAPEX_discounted'].sum().reset_index()
capex_disc_summary = capex_disc_summary.rename(columns={'CAPEX_discounted': 'Discounted CAPEX (US$M)'})


# Merge the discounted capex summary into the overall summary
overall_summary = pd.merge(
    overall_summary, 
    capex_disc_summary, 
    on=['Scenario', 'Version','Asset', 'Case'], 
    how='left'
)


# Filter the CAPEX data for years up to and including 'RFSU (First non-zero production year)'
df_capex = pd.merge(
    df_capex,
    first_non_zero_year,
    on=['Scenario','Version', 'Asset', 'Case'],
    how='left'
)

df_capex_rfsu = df_capex[df_capex['Year'] <= df_capex['RFSU (First non-zero production year)']]

# Calculate total CAPEX up to and including the RFSU year
capex_rfsu_summary = df_capex_rfsu.groupby(['Scenario','Version', 'Asset', 'Case'])['CAPEX_real'].sum().reset_index()
capex_rfsu_summary = capex_rfsu_summary.rename(columns={'CAPEX_real': 'CAPEX up to RFSU (US$M Real)'})


# Merge the CAPEX up to RFSU into the overall summary
overall_summary = pd.merge(
    overall_summary, 
    capex_rfsu_summary, 
    on=['Scenario', 'Version','Asset', 'Case'], 
    how='left'
)

#########################################################################################################################################################################################################################################################
###################### Summary Table Calculations and Output ############################################################################################################################################################################################
#########################################################################################################################################################################################################################################################
# Perform calculations on the summary table
overall_summary.loc[:, 'PWPI'] = overall_summary['NPV10 (USDM)'] / overall_summary['Discounted CAPEX (US$M)']

st.write(overall_summary)

col1, col2, col3, col4 =st.columns(4)

with col1:
    

    # Filter the data
    plot_df = overall_summary.dropna(subset=['IRR (%)', 'PWPI', 'Total_Production_mmboe'])
    plot_df = plot_df[plot_df['Total_Production_mmboe'] > 0]
    
    # Plot
    fig = px.scatter(
        plot_df,
        x='IRR (%)',
        y='PWPI',
        size='Total_Production_mmboe',
        color='Asset',  # Optional: use any grouping column you like
        hover_name='Asset',
        title='Return on Investment (Lifecycle, Unrisked)',
        size_max=60,
        template='plotly_white'
    )
    
    # Show in Streamlit
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write("Chart to come"

