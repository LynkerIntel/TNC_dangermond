library(hydrofabric)

dir <-'/Volumes/MyBook/TNC'
vsi <- "/vsis3/lynker-spatial/gridded-resources"
source_file  <- glue("{dir}/source_hydrofabric.gpkg")
reference_file     <- glue("{dir}/reference_hydorfabric.gpkg")
refactored_file    <- glue("{dir}/refactored_hydorfabric.gpkg")
aggregated_file    <- glue("{dir}/aggregated_hydorfabric.gpkg")
nextgen_file       <- glue("{dir}/tnc_hf/nextgen_hydorfabric.gpkg")
model_atts_file    <- glue("{dir}/tnc_hf/model_attributes.parquet")
model_weights_file <- glue("{dir}/tnc_hf/model_forcing_weights.parquet")
flows_atts_file    <- glue("{dir}/tnc_hf/model_flows.parquet")

cabcm_vars = c("aet", "cwd", "pck", "pet", "rch", "run", "str", "tmn", "tmx")
