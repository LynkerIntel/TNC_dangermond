# CABCM
source("config.R")

geom = read_sf(nextgen_file, "divides")

ncs = list.files(glue('{dir}/SCRV'), pattern = '.nc', full.names = TRUE)

outfiles = glue('{dir}/tnc_hf/water_balance/cabcm/{gsub("nc", "parquet", basename(ncs))}')

for(i in 1:length(ncs)){
  r = rast(ncs[i])
  dd = zonal::execute_zonal(r, geom, ID = "divide_id", join = FALSE) 
  colnames(dd) = c("divide_id", as.character(as.Date(time(r))))
  td = tidyr::pivot_longer(dd, cols = -divide_id, 
                           names_to = "date", 
                           values_to = "value")
  td$var = gsub(".nc", "", basename(ncs[i]))
  td$source = "cabcm_v8"
  arrow::write_parquet(td, outfiles[i])
}

# Terraclim

ncs = list.files(glue('{dir}/terraclim'), pattern = '.nc', full.names = TRUE)
outfiles = glue('{dir}/tnc_hf/water_balance/terraclim/{gsub("nc", "parquet", basename(ncs))}')

for(i in 1:length(ncs)){
  r = rast(ncs[i])
  dd = zonal::execute_zonal(r, geom, ID = "divide_id", join = FALSE) 
  colnames(dd) = c("divide_id", as.character(as.Date(time(r))))
  td = tidyr::pivot_longer(dd, cols = -divide_id, names_to = "date", values_to = "value") |>
    mutate(var = gsub(".nc", "", basename(ncs[i])),
           source = "terraclim") 
  arrow::write_parquet(td, outfiles[i])
}

