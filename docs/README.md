# docs
## GOOS BioEco portal API access

The GOOS BioEco portal provides API access via GeoNode/Django (REST) and GeoServer (WMS/WFS).

### REST

An example of fetching all layers from Python is given here: https://github.com/iobis/bioeco-export/blob/main/lib/api.py#L17. More details are available for each individual layer via the `/api/layers/{id}/` endpoint, see the `resource_uri` property in the full layers list.

Many layer properties in the portal are managed through theasaurus keywords, see here for fetching all keywords from the API: https://github.com/iobis/bioeco-export/blob/main/lib/api.py#L37.

### WFS

Layer geometries are available through WFS. Here's an example in R which fetches all seagrass geometries and writes them to shapefiles. Note the `&viewparams=where:where (array[42] && keywords)` filter which corresponds to the seagrass keyword.

```r
library(sf)
library(dplyr)
library(purrr)

url <- "https://geonode.goosocean.org/geoserver/geonode/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=geonode%3Aall_layers&maxFeatures=10000&outputFormat=application%2Fjson&viewparams=where:where%20(array%5B42%5D%20%26%26%20keywords)"
geo <- st_read(url)

points <- data.frame()
lines <- data.frame()
polygons <- data.frame()

for (i in 1:nrow(geo)) {
  geometry <- st_collection_extract(geo[i,], "POLYGON")
  if (nrow(geometry) > 0) {
    polygons <- rbind(polygons, geometry)
  }
  geometry <- st_collection_extract(geo[i,], "POINT")
  if (nrow(geometry) > 0) {
    points <- rbind(points, geometry)
  }
  geometry <- st_collection_extract(geo[i,], "LINE")
  if (nrow(geometry) > 0) {
    lines <- rbind(lines, geometry)
  }
}

mapview(polygons) + mapview(lines) + mapview(points)

st_write(polygons, dsn = "seagrass_polygons.shp", append = FALSE, layer = "polygons")
st_write(lines, dsn = "seagrass_lines.shp", append = FALSE, layer = "lines")
st_write(points, dsn = "seagrass_points.shp", append = FALSE, layer = "points")
```
