import requests
import geopandas as gpd
import shapely
from requests.exceptions import JSONDecodeError
import logging
import json
from shapely.errors import GEOSException


def download_geojson(layer_name: str):
    geoserver_url = f"https://geonode.goosocean.org/geoserver/geonode/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "maxFeatures": "100000",
        "outputFormat": "application/json"
    }
    headers = {
        "Cookie": "GS_FLOW_CONTROL=GS_CFLOW_-236069a4:196f7f07bdf:-7569; GS_FLOW_CONTROL=GS_CFLOW_-236069a4:196f7f07bdf:-7569; remember-me=YWRtaW4lNDBkZWZhdWx0OjE3NDk0NzM2ODYwNzA6MmRkZTIxMmVlM2M1M2UxOTlmMmJmMTM3NTNjMWRhYzk; JSESSIONID=49DD1B09F2F87ACF791013689AFA41F2; csrftoken=EFxEdUNPp6RosSraJIliV8kDeImGtCkvkm2vsjl39KoqDVvkfezIE8AI0uTFu4a6; sessionid=j2yyckzswesbo2sega08fdk3hgvbgygb"
    }
    res = requests.get(geoserver_url, params=params, headers=headers)
    try:
        geojson = res.json()
        return geojson
    except JSONDecodeError as e:
        logging.error(e)
    return None


def cleanup_geometry(geom, simplify, precision):
    geom_unioned = geom.union_all()
    geom_simplified = geom_unioned.simplify(simplify, preserve_topology=True)
    try:
        wkt = shapely.set_precision(geom_simplified, precision).wkt
    except GEOSException as e:
        wkt = shapely.set_precision(geom_simplified, precision / 10).wkt
    return wkt


def get_wkt(layer_name: str, layer_id: str, mock: bool, simplify: float = 0.0001, precision: float = 0.001) -> str:
    if mock:
        with open(f"geo_data/{layer_id}.json") as f:
            geojson = json.load(f)
    else:
        geojson = download_geojson(layer_name=layer_name)
    if geojson is not None and len(geojson["features"]) > 0:
        crs_urn = geojson.get("crs", {}).get("properties", {}).get("name")
        gdf = gpd.GeoDataFrame.from_features(geojson["features"])
        if crs_urn:
            gdf.set_crs(crs_urn, inplace=True)
        else:
            logging.warning("No CRS found in GeoJSON, assuming EPSG:4326")
            gdf.set_crs("EPSG:4326", inplace=True)
        if gdf.crs.to_epsg() != 4326:
            logging.warning(f"Found CRSS {gdf.crs.to_epsg()}, reprojecting")
            gdf = gdf.to_crs(epsg=4326)
        geom = gdf.geometry.make_valid()
        wkt = cleanup_geometry(geom, simplify, precision)
        return wkt
