## Station Data 
This directory contains code for accessing station data, and will eventually contain
QC and processing code in support of creating a water balance from 1979-2023 


### Details
**Notebooks:**

`./station_query.r` Initial investigation using existing rainOrSnowTools code  
`./station_query.ipynb` Request met station data w/ several APIs.  
`./dendra_query.ipynb` Request data from Dendra, currently grounwater well data  

**Code:**

`./lib` contains the code required to run the notebooks (minimizing notebook code).  
`./lib/data_loaders.py` contains `Dendra` class for querying data.  
`./lib/dendra_berkeley.py` contains older python wrapper.  



**Output:**
Note: `./output` files are stored on aws s3, in `tnc-dangermond`

`./groundwater/gw_catchment_mean_daily_depth`:
> This is a daily-mean time series of groundwater distance, in units of meters.
> It has been been aggregated to the catchment level, so each "divide_id" with
> groundwell data has a singe timeseries representing mean (if N wells > 1) or 
> a single time series if N wells = 1. 


`./groundwater/gw_monthly_delta`:
> Monthly delta (i.e. change in groundwater distance), in units of meters, for comparing groundwell data to model outputs.

`./groundwater/gw_qc_pass`:
> Groundwell data, in units of feet, with 5 minute resolution, that has 
> passed the rudimentary QC methods defined in `./lib/groundwater_qc.py`