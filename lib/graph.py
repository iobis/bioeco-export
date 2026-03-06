import json
from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.namespace import RDF
from pyld import jsonld
from lib.geo import get_wkt
from lib.api import api_layer, api_thesauri, api_keywords
from lib import strip_html_tags
import re
import ast


def generate_graph(layers: dict, mock=False) -> str:
    """Generate a graph from the BioEco GeoNode API data."""

    schema = Namespace("http://schema.org/")
    geosparql = Namespace("http://www.opengis.net/ont/geosparql#")

    # get thesauri

    thesauri = api_thesauri(mock=mock)

    # get generic keywords and build lookup by resource_uri
    keywords_data = api_keywords(mock=mock)
    keyword_lookup = {
        obj["resource_uri"]: obj.get("name")
        for obj in keywords_data.get("objects", [])
    }

    # collect all thesaurus keyword URIs to optionally exclude from generic keywords
    thesaurus_keyword_uris = set()
    for thesaurus in thesauri.values():
        thesaurus_keyword_uris.update(thesaurus.keys())

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

        # generic keywords (not mapped to EOV thesauri)

        if "keywords" in layer_detail and isinstance(layer_detail["keywords"], list):
            for keyword_uri in layer_detail["keywords"]:
                # skip if this keyword URI is already represented in thesauri
                if keyword_uri in thesaurus_keyword_uris:
                    continue

                label = keyword_lookup.get(keyword_uri)
                if label:
                    g.add((subject, schema.keywords, Literal(label)))
                else:
                    # fallback to the URI if we don't have a label
                    g.add((subject, schema.keywords, Literal(keyword_uri)))

        # temporal extent

        temporal_start = layer_detail.get("temporal_extent_start")
        temporal_end = layer_detail.get("temporal_extent_end")

        if temporal_start or temporal_end:
            if temporal_start and temporal_end:
                temporal_value = f"{temporal_start}/{temporal_end}"
            else:
                temporal_value = temporal_start or temporal_end

            g.add((subject, schema.temporalCoverage, Literal(temporal_value)))

        # maintenance frequency

        maintenance_frequency = layer_detail.get("maintenance_frequency")
        if maintenance_frequency:
            mf_prop = BNode()
            g.add((mf_prop, RDF.type, schema.PropertyValue))
            g.add((mf_prop, schema.name, Literal("maintenanceFrequency")))
            g.add((mf_prop, schema.value, Literal(maintenance_frequency)))
            g.add((subject, schema.additionalProperty, mf_prop))

        # funding, funding sector

        funding_text = layer_detail.get("funding")
        funding_sector_raw = layer_detail.get("funding_sector")

        if funding_text or funding_sector_raw:
            grant = BNode()
            g.add((grant, RDF.type, schema.MonetaryGrant))

            if funding_text:
                g.add((grant, schema.description, Literal(funding_text)))

            sectors = []

            if isinstance(funding_sector_raw, list):
                sectors = funding_sector_raw
            elif isinstance(funding_sector_raw, str):
                try:
                    parsed = ast.literal_eval(funding_sector_raw)
                    if isinstance(parsed, list):
                        sectors = parsed
                    else:
                        sectors = [funding_sector_raw]
                except (ValueError, SyntaxError):
                    sectors = [funding_sector_raw]

            for sector in sectors:
                g.add((grant, schema.category, Literal(sector)))

            g.add((subject, schema.funding, grant))

        # project outputs (hasPart as DataDownload)

        outputs_raw = layer_detail.get("outputs")
        if outputs_raw:
            try:
                outputs_list = ast.literal_eval(outputs_raw)
                if isinstance(outputs_list, list):
                    for output_url in outputs_list:
                        dd = BNode()
                        g.add((dd, RDF.type, schema.DataDownload))
                        g.add((dd, schema.contentUrl, Literal(output_url)))
                        g.add((subject, schema.hasPart, dd))
            except (ValueError, SyntaxError):
                # if parsing fails, skip outputs
                pass

        # standard operating procedures

        sops_raw = layer_detail.get("sops")
        if sops_raw:
            try:
                sops_list = ast.literal_eval(sops_raw)
                if isinstance(sops_list, list):
                    for sop_url in sops_list:
                        g.add((subject, schema.publishingPrinciples, Literal(sop_url)))
            except (ValueError, SyntaxError):
                # if parsing fails, skip sops
                pass

        # readiness levels

        if "tkeywords" in layer_detail:
            readiness_thesauri = {
                "readiness-coordination-rdf": "readinessCoordination",
                "readiness-data-rdf": "readinessData",
                "readiness-requirements-rdf": "readinessRequirements",
            }

            for thesaurus_id, readiness_name in readiness_thesauri.items():
                if thesaurus_id not in thesauri:
                    continue

                readiness_dict = thesauri[thesaurus_id]

                for keyword_uri in layer_detail["tkeywords"]:
                    if keyword_uri not in readiness_dict:
                        continue

                    readiness_keyword = readiness_dict[keyword_uri]
                    label = readiness_keyword.get("label") or readiness_keyword.get("alt_label")
                    if not label:
                        continue

                    readiness_node = BNode()
                    g.add((readiness_node, RDF.type, schema.PropertyValue))
                    g.add((readiness_node, schema.name, Literal(readiness_name)))
                    g.add((readiness_node, schema.value, Literal(label)))
                    g.add((subject, schema.additionalProperty, readiness_node))

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
