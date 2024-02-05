import json
import requests
import re


API_URL = "https://geonode.goosocean.org"


def api_layers(mock: bool=True) -> dict:
    """Get layers from the BioEco GeoNode API."""

    if mock:
        with open("api_data/layers.json") as f:
            data = json.load(f)
            return data["objects"]
    else:
        data = requests.get(f"{API_URL}/api/layers/").json()
        return data["objects"]


def api_layer(uri: str, mock: bool=True) -> dict:
    """Get a layer from the BioEco GeoNode API."""

    if mock:
        layer_id = re.search(r"\d+", uri).group(0)
        with open(f"api_data/{layer_id}.json") as f:
            data = json.load(f)
            return data
    else:
        data = requests.get(f"{API_URL}{uri}").json()
        return data
