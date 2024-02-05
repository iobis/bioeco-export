import json
import os
import boto3
from lxml import etree
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF
from pyld import jsonld
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv


def strip_html_tags(text: str) -> str:
    """Strip HTML tags from a string."""
    parser = etree.HTMLParser()
    tree = etree.fromstring(text, parser)
    return etree.tostring(tree, encoding="unicode", method="text")


def api_layers(mock: bool=True) -> dict:
    """Get layers from the BioEco GeoNode API."""
    if mock:
        with open("api.json") as f:
            data = json.load(f)
            return data["objects"]


def generate_graph(layers:dict) -> str:
    """Generate a graph from the BioEco GeoNode API data."""
    schema = Namespace("http://schema.org/")
    geosparql = Namespace("http://www.opengis.net/ont/geosparql#")

    g = Graph()

    for item in layers:
        url = f"https://geonode.goosocean.org/layers/geonode_data:{item['typename']}"
        subject = URIRef(url)
        
        g.add((subject, RDF.type, schema.ResearchProject))
        g.add((subject, schema.name, Literal(item["title"])))
        g.add((subject, schema.url, Literal(url)))
        g.add((subject, schema.description, Literal(strip_html_tags(item["abstract"]))))

        geometry = BNode()
        g.add((subject, geosparql.hasGeometry, geometry))
        g.add((geometry, geosparql.asWKT, Literal(item["csw_wkt_geometry"], datatype=geosparql.wktLiteral)))

        # test cases:
        # - https://geonode.goosocean.org/layers/geonode_data:geonode:NRW_Benthic_Rock_monitoring
        # - https://geonode.goosocean.org/layers/geonode_data:geonode:irish_deepwater_trawl_survey

        # "temporal_extent_end": null,
        # "temporal_extent_start": "2019-01-01T00:00:00",

        # "maintenance_frequency": "annually",

        # "regions":
        # [
        #     "Ireland"
        # ],

        # eovs
        # ebvs
        # other keywords
        # readiness levels
        # funding, funding sector

    doc = g.serialize(format="json-ld")

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
    output = json.dumps(framed, indent=2)
    return output


def upload_file(filename: str):
    """Upload a file to S3."""
    load_dotenv()
    ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
    SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        s3.upload_file(filename, "bioeco-graph", filename)
        print("Upload Successful")
    except FileNotFoundError:
        print("File not found")
    except NoCredentialsError:
        print("Credentials not available")
