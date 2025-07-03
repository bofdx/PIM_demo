import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import gc
import os
from scipy.optimize import newton
from io import StringIO

# Load the CP CubeStringIO
df_CP = pd.read_csv(StringIO(content), delimiter=',')


st.print(df_CP)
