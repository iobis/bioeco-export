from lib.api import api_layer, api_layers
from lib.geo import download_geojson
import json
import re


def populate_geo_cache():
    layers = api_layers(mock=True)

    for layer in layers["objects"]:
        layer_id = re.search(r"\d+", layer["resource_uri"]).group(0)
        typename = layer["typename"]
        print(layer_id, typename)
        geojson = download_geojson(typename)
        if geojson is not None:
            with open(f"geo_data/{layer_id}.json", "w") as f:
                f.write(json.dumps(geojson))
        else:
            print(f"No geojson for {typename}")


populate_geo_cache()
