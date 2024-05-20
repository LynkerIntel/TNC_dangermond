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
    >> `./lib/data_loaders.py` contains `Dendra` class for querying data
    >> `./lib/dendra_berkeley.py` contains older python wrapper 

Note: `./output` files are stored on aws s3, in `tnc-dangermond`