#!/bin/env python3
import os

import networkx
from lxml import etree
from urllib.parse import urlsplit, urlunsplit, SplitResult
import re

here = os.path.abspath(os.path.dirname(__file__))

url_re = re.compile('url\((.*)\)')


def get_element_href(element):
    for name, value in element.attrib.items():
        if name.endswith('href'):
            yield urlsplit(value)
        else:
            match = url_re.match(value)
            if match:
                yield urlsplit(match.group(1))


def get_descendant_hrefs(element):
    yield from get_element_href(element)
    for e in element.iterdescendants():
        yield from get_element_href(e)


def load_all_elements(*paths):
    elements_by_url = {}
    for path in paths:
        root = etree.parse(path).getroot()
        relpath = os.path.relpath(path, here)
        for e in root.iterdescendants():
            if e.get('id'):
                url = SplitResult('', '', relpath, '', e.get('id'))
                elements_by_url[url] = e
    return elements_by_url


def generate_dependency_graph(elements_by_url):
    urls_by_element = {v: k for k, v in elements_by_url.items()}
    g = networkx.DiGraph()
    g.add_nodes_from(elements_by_url.values())
    for node in g:
        node_url = urls_by_element[node]
        for dep_href in get_descendant_hrefs(node):
            if not dep_href.path:
                dep_href = dep_href._replace(path=node_url.path)
            g.add_edge(elements_by_url[dep_href], node)
    return g


if __name__ == '__main__':
    elements_by_url = load_all_elements(
        os.path.join(here, '..', 'src', 'defs.svg'))
    g = generate_dependency_graph(elements_by_url)
    for n in g:
        print(n.get('id'), {x.get('id') for x in networkx.ancestors(g, n)})
