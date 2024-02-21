from lib import *
from lib.graph import generate_graph
from lib.api import api_layers, api_layer, api_thesaurus_keywords, api_eovs


layers = api_layers(mock=True)
graph = generate_graph(layers[:10], mock=True)

with open("bioeco_graph.jsonld", "w") as f:
    f.write(graph)

# upload_file("bioeco_graph.jsonld")

