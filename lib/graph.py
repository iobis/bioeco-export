import json
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF
from pyld import jsonld
from lib.geo import get_wkt
from lib.api import api_layer, api_thesauri
from lib import strip_html_tags
import re


def generate_graph(layers: dict, mock=False) -> str:
    """Generate a graph from the BioEco GeoNode API data."""

    schema = Namespace("http://schema.org/")
    geosparql = Namespace("http://www.opengis.net/ont/geosparql#")

    # get thesauri

    thesauri = api_thesauri(mock=mock)

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

        # geometry (legacy, bounding box)
        # geometry = BNode()
        # g.add((subject, geosparql.hasGeometry, geometry))
        # g.add((geometry, geosparql.asWKT, Literal(layer_detail["csw_wkt_geometry"], datatype=geosparql.wktLiteral)))

        # geometry (shape)

        typename = layer_detail["typename"]
        if typename is not None:
            layer_id = re.search(r"\d+", layer["resource_uri"]).group(0)
            geometry = get_wkt(typename, layer_id, mock=mock)
            if geometry is not None:
                geometry_node = BNode()
                g.add((subject, geosparql.hasGeometry, geometry_node))
                g.add((geometry_node, geosparql.asWKT, Literal(geometry, datatype=geosparql.wktLiteral)))

        # eovs

        if "tkeywords" in layer_detail:

            layer_eovs = [thesauri["eovs-rdf"][item] for item in layer_detail["tkeywords"] if item in thesauri["eovs-rdf"]]
            layer_subvariables = [thesauri["eov-subvariables-rdf"][item] for item in layer_detail["tkeywords"] if item in thesauri["eov-subvariables-rdf"]]
            layer_othervariables = [thesauri["eovs-other-rdf"][item] for item in layer_detail["tkeywords"] if item in thesauri["eovs-other-rdf"]]

            if len(layer_eovs) > 0:
                for variable in layer_eovs:
                    vm = BNode()
                    g.add((vm, RDF.type, schema.PropertyValue))
                    g.add((vm, schema.name, Literal(variable["label"])))
                    g.add((vm, schema.propertyID, Literal(variable["about"])))
                    g.add((subject, schema.variableMeasured, vm))

            if len(layer_subvariables) > 0:
                for variable in layer_subvariables:
                    vm = BNode()
                    g.add((vm, RDF.type, schema.PropertyValue))
                    g.add((vm, schema.name, Literal(variable["label"])))
                    g.add((vm, schema.propertyID, Literal(variable["about"])))
                    g.add((subject, schema.variableMeasured, vm))

            if len(layer_othervariables) > 0:
                for variable in layer_othervariables:
                    vm = BNode()
                    g.add((vm, RDF.type, schema.PropertyValue))
                    g.add((vm, schema.name, Literal(variable["label"])))
                    g.add((vm, schema.propertyID, Literal(variable["about"])))
                    g.add((subject, schema.variableMeasured, vm))

        # temporal extent

        temporal_start = layer_detail.get("temporal_extent_start")
        temporal_end = layer_detail.get("temporal_extent_end")

        if temporal_start or temporal_end:
            if temporal_start and temporal_end:
                temporal_value = f"{temporal_start}/{temporal_end}"
            else:
                temporal_value = temporal_start or temporal_end

            g.add((subject, schema.temporalCoverage, Literal(temporal_value)))



        # readiness levels
        # readiness-coordination-rdf
        # readiness-data-rdf
        # readiness-requirements-rdf

        # "maintenance_frequency": "annually",

        # "regions":
        # [
        #     "Ireland"
        # ],

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
