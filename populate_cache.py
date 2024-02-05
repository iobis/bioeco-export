from lib.api import api_layer, api_layers
import json
import re


def populate_cache():
    layers = api_layers(mock=False)

    with open(f"api_data/layers.json", "w") as f:
        f.write(json.dumps(layers, indent=2))

    for layer in layers:
        layer_data = api_layer(layer["resource_uri"], mock=False)
        layer_id = re.search(r"\d+", layer["resource_uri"]).group(0)
        print(layer_id)

        with open(f"api_data/{layer_id}.json", "w") as f:
            f.write(json.dumps(layer_data, indent=2))


populate_cache()
