from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import FOAF, RDF
import json
from lxml import etree
from pyld import jsonld
import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# namespaces

schema = Namespace("http://schema.org/")
geosparql = Namespace("http://www.opengis.net/ont/geosparql#")

# read API data

def strip_html_tags(text):
    parser = etree.HTMLParser()
    tree = etree.fromstring(text, parser)
    return etree.tostring(tree, encoding="unicode", method="text")

with open("api.json") as f:
    data = json.load(f)

# generate graph

g = Graph()

for item in data["objects"][:3]:
    url = f"https://geonode.goosocean.org/layers/geonode_data:{item['typename']}"
    subject = URIRef(url)
    
    g.add((subject, RDF.type, schema.ResearchProject))
    g.add((subject, schema.name, Literal(item["title"])))
    g.add((subject, schema.url, Literal(url)))
    g.add((subject, schema.description, Literal(strip_html_tags(item["abstract"]))))

    geometry = BNode()
    wkt = BNode()
    g.add((subject, geosparql.hasGeometry, geometry))
    g.add((geometry, geosparql.asWKT, Literal(item["csw_wkt_geometry"], datatype=geosparql.wktLiteral)))

doc = g.serialize(format="json-ld")
print(doc)

# framing

frame = {
    "@context": {
        "schema": "http://schema.org/",
        "geosparql": "http://www.opengis.net/ont/geosparql#"
    },
    "@type": "schema:ResearchProject",
    "geosparql:hasGeometry": {
        "geosparql:asWKT": {}
    }
}
framed = jsonld.frame(json.loads(doc), frame)

# output

output = json.dumps(framed, indent=2)
with open("bioeco_graph.jsonld", "w") as f:
    f.write(output)

# upload to https://bioeco-graph.s3.amazonaws.com/bioeco_graph.jsonld

load_dotenv()
ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

try:
    response = s3.upload_file("bioeco_graph.jsonld", "bioeco-graph", "bioeco_graph.jsonld")
    print("Upload Successful")
except FileNotFoundError:
    print("File not found")
except NoCredentialsError:
    print("Credentials not available")
