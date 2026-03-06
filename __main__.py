from lib.graph import generate_graph
from lib.api import api_layers
from lib import upload_file
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG)


layers = api_layers(mock=True)["objects"]
graph = generate_graph(layers, mock=True)

with open("bioeco_graph.jsonld", "w") as f:
    f.write(graph)

upload_file("bioeco_graph.jsonld")
