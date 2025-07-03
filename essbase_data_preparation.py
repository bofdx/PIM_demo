import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import gc
import os
from scipy.optimize import newton
from io import StringIO

col1, col2, col3, col4 =st.columns(4)

with col1:
    reference_year = st.number_input("Reference Year", value=2025, step=1, format="%d")
with col2:
    mid_year_discounting = st.selectbox("Discounting Type:", ["Mid-Year", "End of Year"], index=0)
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

# Reference year and discount rate
discount_rate = 0.1
inflation_rate = 0.022

# Calculate Discount_Factor using mid-year discounting
df_essbase['Discount_Factor'] = 1 / ((1 + discount_rate) ** (df_essbase['Year'] - reference_year + 0.5))
df_essbase['Real_Discount_Factor'] = 1/((1+inflation_rate)**(df_essbase['Year'] - reference_year + 0.5))

################### SECTION TO SUM TOCS -TO BE ADDED ##############################################################################################################





################### SECTION TO CALCULATE INCREMENTALS TO BE ADDED #################################################################################################
st.write(df_essbase)





