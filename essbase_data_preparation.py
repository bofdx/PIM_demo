import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import gc
import os
from scipy.optimize import newton
from io import StringIO

Datafile = "Dummy_Data.csv"

# Load the CP CubeStringIO
df_CP = pd.read_csv(Datafile, delimiter=',')


st.print(df_CP)
