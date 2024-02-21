import json
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF
from pyld import jsonld
from lib import *
from lib.api import api_layer, api_eovs


def generate_graph(layers:dict, mock=False) -> str:
    """Generate a graph from the BioEco GeoNode API data."""

    schema = Namespace("http://schema.org/")
    geosparql = Namespace("http://www.opengis.net/ont/geosparql#")

    # get eov map

    eovs = api_eovs()

    # build graph

    g = Graph()

    for layer in layers:

        # get later detail from API
        
        layer_detail = api_layer(layer["resource_uri"], mock=mock)

        # create url

        url = f"https://geonode.goosocean.org/layers/geonode_data:{layer_detail['typename']}"

        # add triples

        subject = URIRef(url)
        
        g.add((subject, RDF.type, schema.ResearchProject))
        g.add((subject, schema.name, Literal(layer_detail["title"])))
        g.add((subject, schema.url, Literal(url)))
        g.add((subject, schema.description, Literal(strip_html_tags(layer_detail["abstract"]))))

        # geometry

        geometry = BNode()
        g.add((subject, geosparql.hasGeometry, geometry))
        g.add((geometry, geosparql.asWKT, Literal(layer_detail["csw_wkt_geometry"], datatype=geosparql.wktLiteral)))

        # eovs

        if "tkeywords" in layer_detail:
            layer_eovs = [eovs[eov] for eov in layer_detail["tkeywords"] if eov in eovs]

            if len(layer_eovs) > 0:
                for eov in layer_eovs:
                    vm = BNode()
                    g.add((vm, RDF.type, schema.PropertyValue))
                    g.add((vm, schema.name, Literal(eov["label"])))
                    g.add((vm, schema.propertyID, Literal(eov["about"])))
                    g.add((subject, schema.variableMeasured, vm))

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

    # serialize

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
