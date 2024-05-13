# DR 20240509 
# Testing data retrieval. `access_meteo` only
# returns selected met vars, with user selection
# not implented yet. Still useful for locating 
# nearby sites.

# remotes::install_github("mikejohnson51/AOI") 
# remotes::install_github("mikejohnson51/climateR")

# # install.packages("devtools")
# # Install location is here for now...
# devtools::install_github("SnowHydrology/rainOrSnowTools",
#                          ref = "add_meteo_gpm")

library("terra")
library(climateR)
library(rainOrSnowTools)

# example vars
met_network <- "ALL"
datetime <- as.POSIXct("2020-01-01 00:00:00", tz = "UTC")
time_s <- 86400
# dangermond approx centroid
lon <- -120.44449
lat <- 34.51052
distance_m <- 40000 # 40km
# degree_filter <- 1

# get data w/ example locs
meteo <- access_meteo(networks = met_network,
                      datetime_utc_obs = datetime, 
                      lon_obs = lon, 
                      lat_obs = lat,
                      dist_thresh_m = distance_m,
                      time_thresh_s = time_s)
print(head(meteo))