from lib import *


layers = api_layers()
output = generate_graph(layers)

with open("bioeco_graph.jsonld", "w") as f:
    f.write(output)

upload_file("bioeco_graph.jsonld")
