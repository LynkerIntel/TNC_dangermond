
# Define Santa Clara River Valley -----------------------------------------

library(sf)

read_sf('/Volumes/MyBook/TNC/footprint_childrenBoundingBox_children.kml') |>
  st_collection_extract("POLYGON") |> 
  filter(Name == "footprint.3476842") |>
  st_make_valid() |>
  write_sf("/Volumes/MyBook/TNC/SCRV.gpkg")


