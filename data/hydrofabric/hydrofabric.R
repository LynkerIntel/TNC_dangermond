source("config.R")
devtools::load_all('/Users/mikejohnson/github/hydrofab')
jldp = st_buffer(read_sf(glue('{dir}/tnc.geojson')), 500)

# Flowlines ---------------------------------------------------------------

fl = read_sf(source_file, "flowlines")

UT_COMIDs = filter(fl, fl$TerminalFl == 1) %>% 
  st_filter(st_transform(jldp, st_crs(fl))) %>% 
  pull(COMID) %>% 
  lapply(get_UT, network = fl) %>% 
  unlist() %>% 
  unique()

flowpaths = filter(fl, COMID %in% UT_COMIDs) %>% 
  select(-Permanent_Identifier) %>% 
  get_tocomid() |>
  st_cast("LINESTRING") |> 
  rename_geometry("geometry") %>%
  mutate(lengthkm = hydrofab::add_lengthkm(.))

# Divides -----------------------------------------------------------------

div = read_sf(glue('{dir}/source_hydrofabric.gpkg'), "divides") 

dendritic = filter(div,  FEATUREID %in% flowpaths$comid) %>% 
  mutate(type = "network")

non_dendritic = filter(div, !FEATUREID %in% filter(fl, StreamOrde > 0)$COMID) %>% 
  st_filter(st_transform(jldp, st_crs(fl))) %>% 
  mutate(type = "coastal")
  
network = bind_rows(non_dendritic, dendritic) 

divides = clean_geometry(network, ID = "FEATUREID", keep = .5) |>
  select(featureid = FEATUREID, type) %>% 
  st_make_valid() %>%
  mutate(areasqkm = hydrofab::add_areasqkm(.))

map_ids = data.frame(old = unique(c(flowpaths$comid, divides$featureid))) %>% 
  mutate(new = 1:n())

flowpaths$comid   = map_ids$new[match(flowpaths$comid,   map_ids$old)] 
flowpaths$tocomid = map_ids$new[match(flowpaths$tocomid, map_ids$old)] 
divides$featureid = map_ids$new[match(divides$featureid, map_ids$old)] 

write_sf(flowpaths, reference_file, "flowpath", overwrite = TRUE)
write_sf(divides,   reference_file, "divides",  overwrite = TRUE)

# Geoprocess --------------------------------------------------------------------

fps = read_sf(reference_file, "flowpath")
div = read_sf(reference_file, "divides") %>% filter(type == "network")

refactor(flowpaths = fps,
         catchments = div,
         fac = glue('{dir}/fac.tif'),
         fdr = glue('{dir}/fdr.tif'),
         split_flines_meters = 5000,
         collapse_flines_meters = 100,
         collapse_flines_main_meters = 100,
         outfile = refactored_file)

aggregate_to_distribution(
  gpkg = refactored_file,
  ideal_size_sqkm = 1,
  min_length_km = .1,
  min_area_sqkm = .5,
  outfile = aggregated_file,
  overwrite = TRUE
)

coastal =  read_sf(reference_file, "divides") %>% filter(type != "network") %>% 
  rename(divide_id = featureid) %>% 
  st_transform(5070)

rfc = read_sf(aggregated_file, "divides") %>% 
  bind_rows(coastal)  %>% 
  mutate(areasqkm = hydrofab::add_areasqkm(.)) %>% 
  write_sf(aggregated_file, "divides", overwrite = TRUE)

# NextGen --------------------------------------------------------------------

apply_nexus_topology(aggregated_file, export_gpkg = nextgen_file)

tnc = read_sf(nextgen_file, "divides") 

reference_fabric = open_dataset('/Users/mikejohnson/hydrofabric/v2.2/reference/conus_divides') %>% 
  filter(vpuid == "18") %>% 
  read_sf_dataset() %>% 
  st_filter(tnc)

ints = st_intersection(select(tnc, small_area = areasqkm, divide_id), 
                       select(reference_fabric, comid = id, big_area = areasqkm)) %>% 
  mutate(int_area = add_areasqkm(.)) %>% 
  st_drop_geometry() %>%
  group_by(divide_id) %>% 
  mutate(artifical_big_area = sum(int_area)) %>% 
  ungroup() %>% 
  mutate(ratio = int_area / artifical_big_area) %>% 
  select(comid, divide_id, ratio) %>% 
  distinct()

flowline_mapping = open_dataset('/Users/mikejohnson/hydrofabric/v2.2/reference/conus_network') %>% 
  select(hf_id, hydroseq) %>% 
  right_join(ints, by = c("hf_id" = "comid")) %>% 
  collect()

# Model Weights and Parameters --------------------------------------------

# Divides for NextGen Fabric
div <- read_sf(nextgen_file, "divides")

# NOAH OWP Variables (Grid -> Polygon)
nom_vars <- c("bexp", "dksat", "psisat", "smcmax", "smcwlt")

# Read the first layer of each from the remote COG Store
# No need oto crop here as only the connection is being established
r = rast(glue("{vsi}/nwm/conus/{nom_vars}.tif"), 
         lyrs = seq(1,length(nom_vars)*4, by = 4))

# Get Mode Beta parameter
modes = execute_zonal(r[[1]], 
                      fun = mode,
                      div, ID = "divide_id", 
                      join = FALSE)  %>% 
  setNames(gsub("fun.", "", names(.)))

# Get Geometric Mean of Saturated soil hydraulic conductivity, 
# and matric potential
gm = execute_zonal(r[[2:3]], 
                   fun = geometric_mean,
                   div, ID = "divide_id", 
                   join = FALSE)  %>% 
  setNames(gsub("fun.", "", names(.)))

# Get Mean Saturated value of soil moisture and Wilting point soil moisture
m = execute_zonal(r[[4:5]], 
                  fun = "mean",
                  div, ID = "divide_id", 
                  join = FALSE)  %>% 
  setNames(gsub("mean.", "", names(.)))


# Merge all tables into one
d1 <- powerjoin::power_full_join(list(modes, gm, m), by = "divide_id")

# GWBUCKET Rescale Data  (Polygon --> Polygon) --------------------------------

d2 <- open_dataset(glue("/Users/mikejohnson/hydrofabric/v2.2/reference/conus_routelink")) |>
  select(hf_id , starts_with("gw_")) |>
  inner_join(mutate(flowline_mapping, hf_id = as.integer(hf_id)), by = "hf_id") |>
  group_by(divide_id) |>
  collect() |>
  summarize(
    gw_Coeff =weighted.mean(gw_Coeff, 
                                   w = ratio, 
                                   na.rm = TRUE),
    gw_Zmax  = weighted.mean(gw_Zmax_mm,  
                                      w = ratio, 
                                      na.rm = TRUE),
    gw_Expon = mode(floor(gw_Expon))
  )

# Forcing Downscaling Base Data
## Centroid 

d3 <- st_centroid(div) |>
  st_transform(4326) |>
  st_coordinates() |>
  data.frame() |>
  mutate(divide_id = div$divide_id)

## Elevation derived inputs

dem = rast('/Volumes/MyBook/TNC/dem.tif')

r = c(dem, terra::terrain(dem, v = "slope"),  terra::terrain(dem, "aspect"))

d4 <- execute_zonal(r[[1]], 
                    div, 
                    ID = "divide_id", 
                    join = FALSE) |>
  setNames(c("divide_id", "elevation_mean"))

d5 <- execute_zonal(r[[2]], 
                    div, 
                    ID = "divide_id", 
                    join = FALSE) |>
  setNames(c("divide_id","slope_mean"))

d6 <- execute_zonal(r[[3]], 
                    div, ID = "divide_id", fun = circular_mean, 
                    join = FALSE) |>
  setNames(c("divide_id", "aspect_c_mean"))


model_attributes <- powerjoin::power_full_join(list(d1, d2, 
                                                    d3, d4, 
                                                    d5, d6), 
                                               by = "divide_id")

# Build a Forcing Weights File --------------------------------------------

type = "medium_range.forcing"

w = weight_grid(rast(glue('{vsi}/{type}.tif')), div, ID = "divide_id") |> 
  mutate(grid_id = type)

# Flows 
nat_flows = read.csv(glue('{dir}/flow_17593969_17593369_17593405_17593353_17593255_mean_estimated_1979_2024.csv'))  %>% 
  mutate(date = as.Date(paste(year, month, "01", sep = '-'))) %>% 
  select(comid, date, flow = value)

r = flowline_mapping %>% 
  select(hf_id, divide_id, hydroseq) %>% 
  group_by(divide_id) %>% 
  slice_min(hydroseq) %>% 
  ungroup() 

xx2 = read_sf(nextgen_file, "network") %>% 
  select(id, toid,  divide_id) %>% 
  left_join(r) %>% 
  distinct() %>% 
  left_join(nat_flows, by = c("hf_id" = "comid"),  relationship = "many-to-many")

# Write it all out --------------------------------------------------------
write_parquet(w, model_weights_file)
write_parquet(model_attributes, model_atts_file)
write_parquet(xx2, flows_atts_file)



s = '/Users/mikejohnson/hydrofabric/v2.2'

tnc = read_sf(nextgen_file, "divides") %>% 
  select(small_area = areasqkm, id)

reference_fabric = open_dataset(glue('{s}/reference/conus_divides')) %>% 
  filter(vpuid == "18") %>% 
  select(comid = id, big_area = areasqkm, geom) %>% 
  read_sf_dataset() %>% 
  st_filter(tnc) 

ints = st_intersection(tnc, reference_fabric) %>% 
  mutate(int_area = add_areasqkm(.)) %>% 
  st_drop_geometry() %>%
  group_by(id) %>% 
  mutate(artifical_big_area = sum(int_area)) %>% 
  ungroup() %>% 
  mutate(ratio = int_area / artifical_big_area) %>% 
  select(comid, id, ratio) %>% 
  distinct() %>% 
  mutate(comid = as.integer(comid)) %>% 
  filter(complete.cases(.))

rl_mapping = open_dataset(glue('{s}/conus_routelink')) %>%
  select(hf_id, starts_with("rl_")) %>%
  inner_join(ints, by = c("hf_id" = "comid")) %>% 
  collect() %>% 
  group_by(id) %>%
  summarize(across(everything(), ~ round( weighted.mean(x = ., w = ratio, na.rm = TRUE), 8))) %>%
  select(-hf_id, -rl_Length_m, -ratio)

names(rl_mapping) = gsub("rl_", "", names(rl_mapping)) %>% 
  strsplit('_') %>% 
  sapply("[[",1)

rl_mapping = read_sf(nextgen_file, "flowpaths") %>% 
  select(lengthkm, id) %>% 
  st_drop_geometry() %>% 
  mutate(length_m = lengthkm * 1000) %>% 
  select(id, length_m) %>% 
  right_join(rl_mapping)

# flowpath attributes
rl_gages = '11120600'

x = dataRetrieval::findNLDI(nwis = rl_gages)[[1]] %>% 
  st_as_sf(c('X', 'Y'), crs = 4326) %>% 
  st_transform(5070) %>% 
  st_intersection(tnc) %>% 
  st_drop_geometry() %>% 
  mutate(rl_gages = gsub("USGS-", "", identifier)) %>% 
  select(id, rl_gages) %>% 
  right_join(rl_mapping)

write_sf(x, nextgen_file, "flowpath_attributes", overwrite = T)


