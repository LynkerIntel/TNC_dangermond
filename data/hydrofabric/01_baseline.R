library(AOI)
library(nhdplusTools)
library(dplyr)
library(sf)
library(glue)

# Get NHDHighRes as a seed ------------------------------------------------

huc4 = geocode("Jalama Rd, Lompoc, CA 93436", pt = TRUE) %>% 
  get_huc(type = "huc04") %>% 
  pull(huc4)


download_dir <- download_nhdplushr(dir, huc4)

get_nhdplushr(download_dir,
              glue("{download_dir}/nhdplushr_{huc4}.gpkg"),
              layers = NULL, overwrite = TRUE)


# --- Read in SCV bound

AOI = read_sf(glue("/Volumes/MyBook/TNC/SCRV.gpkg")) %>% 
  st_transform(4269) 


fl  = read_sf(glue("{download_dir}/nhdplushr_{huc4}.gpkg"), "NHDflowline")  |>
  st_filter(AOI)

div = read_sf(glue("{download_dir}/nhdplushr_{huc4}.gpkg"), "NHDPlusCatchment")  |>
  st_make_valid() |>
  st_filter(AOI)

wbs = read_sf(glue("{download_dir}/nhdplushr_{huc4}.gpkg"), "NHDWaterbody")  |>
  st_make_valid() |>
  st_filter(AOI)

pois = read_sf('/Volumes/MyBook/conus-hydrofabric/conus_hl.gpkg') |>
  st_transform(4269) |>
  st_filter(AOI)

write_sf(fl,   glue('{dir}/source_hydrofabric.gpkg'), "flowlines")
write_sf(wbs,  glue('{dir}/source_hydrofabric.gpkg'), "waterbodies")
write_sf(div,  glue('{dir}/source_hydrofabric.gpkg'), "divides")
write_sf(pois, glue('{dir}/source_hydrofabric.gpkg'), "hydrolocations")

library(terra)

fac = rast('/Volumes/MyBook/TNC/18/HRNHDPlusRasters1806/fac.tif')
aoi_proj = project(vect(AOI),crs(fac))

fac = crop(fac, aoi_proj, snap = "out")

fdr =  crop(rast('/Volumes/MyBook/TNC/18/HRNHDPlusRasters1806/fdr.tif') , aoi_proj, snap = "out")
dem =  crop(rast('/Volumes/MyBook/TNC/18/HRNHDPlusRasters1806/hydrodem.tif') , aoi_proj, snap = "out")

writeRaster(fac, glue('{dir}/fac.tif'), overwrite = TRUE)
writeRaster(fdr, glue('{dir}/fdr.tif'), overwrite = TRUE)
writeRaster(dem, glue('{dir}/dem.tif'), overwrite = TRUE)
