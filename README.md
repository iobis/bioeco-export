# bioeco-export

Exports the GOOS BioEco graph as JSON-LD to <https://bioeco-graph.s3.amazonaws.com/bioeco_graph.jsonld>.

## How to

- Run `populate_cache.py` to populate the disk based API cache
- Run the other scripts with `mock=True` to use the disk cache
