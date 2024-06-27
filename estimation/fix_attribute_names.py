import pandas as pd

input = "tnc_hf/model_attributes.parquet"

"""
['divide_id', 'bexp_soil_layers_stag=1', 'dksat_soil_layers_stag=1',
       'psisat_soil_layers_stag=1', 'smcmax_soil_layers_stag=1',
       'smcwlt_soil_layers_stag=1', 'gw_Coeff', 'gw_Zmax', 'gw_Expon', 'X',
       'Y', 'elevation_mean', 'slope_mean', 'aspect_c_mean'],
"""

df = pd.read_parquet(input)
mapping = {'slope_mean':'slope'}
df = df.rename(columns=mapping)
df.to_parquet("tnc_hf/model_attributes_fixed.parquet")