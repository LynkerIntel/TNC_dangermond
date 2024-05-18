## Station Data 
This directory contains code for accessing station data, and will eventually contain
QC and processing code in support of creating a water balance from 1979-2023 


### Details
`./station_query.r` Initial investigation using existing rainOrSnowTools code  
`./station_query.ipynb` Request data w/ several APIs. 


`./lib/data_loaders` utilites for interfacing with the Dendra API (note: the Dendra class is overkill for just pulling data, but will come in handy for the dashboard)

Note: `./output` files are stored on aws s3 