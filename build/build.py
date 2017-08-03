import os

import networkx
from lxml import etree
import re

here = os.path.abspath(os.path.dirname(__file__))

url_re = re.compile('url\((.*)\)')


def get_element_href(element):
    for name, value in element.attrib.items():
        if name.endswith('href'):
            yield value
        else:
            match = url_re.match(value)
            if match:
                yield match.group(1)


def get_descendant_hrefs(element):
    yield from get_element_href(element)
    for e in element.iterdescendants():
        yield from get_element_href(e)


def generate_dependency_graph(root):
    g = networkx.DiGraph()
    elements_by_id = {
        e.get('id'): e for e in root.iterdescendants() if e.get('id')}
    g.add_nodes_from(elements_by_id.values())
    for node in g:
        for dep_href in get_descendant_hrefs(node):
            # FIXME: we need to normalise our hrefs and handle cross-file links
            g.add_edge(elements_by_id[dep_href[1:]], node)
    return g


def get_dependencies(dep_graph, elem):
    pass


if __name__ == '__main__':
    # FIXME: this should handle multiple input files
    defs = etree.parse(os.path.join(here, '..', 'src', 'defs.svg')).getroot()
    g = generate_dependency_graph(defs)
    for n in g:
        print(n.get('id'), {x.get('id') for x in networkx.ancestors(g, n)})
