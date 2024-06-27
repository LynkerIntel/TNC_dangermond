library(hydrofabric)

dir <-'/Volumes/MyBook/TNC'
vsi <- "/vsis3/lynker-spatial/gridded-resources"
source_file  <- glue("{dir}/source_hydrofabric.gpkg")
reference_file     <- glue("{dir}/reference_hydrofabric.gpkg")
refactored_file    <- glue("{dir}/refactored_hydrofabric.gpkg")
aggregated_file    <- glue("{dir}/aggregated_hydrofabric.gpkg")
nextgen_file       <- glue("{dir}/tnc_hf/nextgen_hydrofabric.gpkg")
model_atts_file    <- glue("{dir}/tnc_hf/model_attributes.parquet")
model_weights_file <- glue("{dir}/tnc_hf/model_forcing_weights.parquet")
flows_atts_file    <- glue("{dir}/tnc_hf/model_flows.parquet")

cabcm_vars = c("aet", "cwd", "pck", "pet", "ppt", "rch", "run", "str", "tmn", "tmx")
