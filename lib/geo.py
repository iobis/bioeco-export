import requests
import geopandas as gpd
import shapely
from requests.exceptions import JSONDecodeError
import logging


def fetch_geometry(layer_name: str, simplify: float = 0.0001, precision: float = 0.001) -> str:

    geoserver_url = f"https://geonode.goosocean.org/geoserver/geonode/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={layer_name}&maxFeatures=100000&outputFormat=application%2Fjson"
    res = requests.get(geoserver_url)

    try:
        geojson = res.json()
        if len(geojson["features"]) > 0:
            gdf = gpd.GeoDataFrame.from_features(geojson["features"])
            geom = gdf.geometry.make_valid()
            geom_unioned = geom.union_all()
            geom_simplified = geom_unioned.simplify(simplify, preserve_topology=True)
            wkt = shapely.set_precision(geom_simplified, precision).wkt
            return wkt
    except JSONDecodeError as e:
        logging.error(e)

    return None
