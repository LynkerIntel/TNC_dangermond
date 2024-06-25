source("config.R")

# CABCM -------------------------------------------------------------------
## Source: https://www.sciencebase.gov/catalog/item/60e63693d34e2a7685cf644a
## Must manually download or have SB creds

base = glue('{dir}/SCRV/')

for (i in 1:length(cabcm_vars)) {
  df <- data.frame(file = list.files(glue(
    "{base}/{cabcm_vars[i]}_SCRV_monthly"
  ),
  full.names = TRUE))  %>%
    mutate(
      year  = substr(basename(file), 4, 7),
      month  = substr(basename(file), 8, 10),
      date = as.Date(paste(month, "01", year, sep = "-"), format = "%b-%d-%Y")
    ) %>%
    arrange(date) %>%
    filter(date >= as.Date("1979-01-01"))
  
  r = rast(df$file)
  time(r) = df$date
  crs(r) = "EPSG:3310"
  
  writeCDF(r, glue("{base}/{cabcm_vars[i]}.nc"), overwrite = TRUE)
  message(cabcm_vars[i])
}
