#!/bin/env python3
import os
from collections.abc import MutableMapping
import errno

import networkx
from lxml import etree
from urllib.parse import urlsplit, urlunsplit, SplitResult
import re
import argh

here = os.path.abspath(os.path.dirname(__file__))

url_re = re.compile('url\((.*)\)')
namespace_re = re.compile('{.*}')


class NamespacePreservingMap(MutableMapping):
    '''
    lxml's element.attrib dict doesn't make handling element attributes with
    namespaces at all easy. This abstraction tries to make it easier to deal
    with that.

    NB. this won't handle tags with the same name from different namespaces
    '''

    def __init__(self, element):
        self._element = element
        self._keymap = {strip_ns(k): k for k in element.attrib}

    def __getitem__(self, key):
        return self._element.attrib[self._keymap[key]]

    def __setitem__(self, key, value):
        self._element.attrib[self._keymap[key]] = value

    def __delitem__(self, key):
        del self._element.attrib[self._keymap[key]]

    def __len__(self):
        return len(self._element.attrib)

    def __iter__(self):
        return iter(self._keymap)

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, dict(self))


elem_attrs = NamespacePreservingMap


def elem_descendants(element):
    yield element
    yield from element.iterdescendants()


def strip_ns(string):
    # FIXME: see etree.QName
    return namespace_re.sub('', string)


def get_element_hrefs(element):
    for name, value in elem_attrs(element).items():
        if name == 'href':
            yield urlsplit(value)
        else:
            match = url_re.match(value)
            if match:
                yield urlsplit(match.group(1))


def get_descendant_hrefs(element):
    for e in elem_descendants(element):
        yield from get_element_hrefs(e)


def load_all_elements(paths):
    elements_by_url = {}
    for path in paths:
        root = etree.parse(path).getroot()
        realpath = os.path.realpath(path)
        for e in root.iterdescendants():
            if e.get('id'):
                url = SplitResult('', '', realpath, '', e.get('id'))
                if url in elements_by_url:
                    raise NameError(
                        'Element {} already exists'.format(urlunsplit(url)))
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
    if tuple(networkx.simple_cycles(g)):
        raise TypeError('Dependency cycles!')
    return g


def file_paths_under(root_path):
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def ensure_dir(path, hint=''):
    if not os.path.isdir(path):
        if hint:
            hint += ': '
        raise TypeError('{}{} is not a directory'.format(hint, path))


def find_all(element, tag):
    '''
    Similar to element.findall(), except we strip namespaces off tags.
    '''
    for e in element.iterdescendants():
        if strip_ns(e.tag) == tag:
            yield e


def first(i):
    try:
        return next(iter(i))
    except StopIteration as e:
        raise IndexError('No first element') from e


def find_first(element, tag):
    return first(find_all(element, tag))


def makedirs(path):
    try:
        os.makedirs(path)
    except IOError as e:
        if e.errno != errno.EEXIST:
            raise


def open_with_dirs(file_path, mode):
    makedirs(os.path.dirname(file_path))
    return open(file_path, mode)


def build_file(path, elements_by_url, dep_graph):
    tree = etree.parse(path)
    root = tree.getroot()
    to_add_to_def = set()
    for element in elem_descendants(root):
        if strip_ns(element.tag) == 'use':
            attrs = elem_attrs(element)
            href = urlsplit(attrs['href'])
            if not href.netloc:
                # We only rewrite local resources.
                # Normalise path:
                href = href._replace(path=os.path.realpath(
                    os.path.join(os.path.dirname(path), href.path)))

                dependency = elements_by_url[href]
                to_add_to_def.add(dependency)
                to_add_to_def.update(networkx.ancestors(dep_graph, dependency))

                # Rewrite the url to point to the inlined asset:
                # FIXME: this won't handle two elements with the same id
                # attribute referenced in different files
                attrs['href'] = urlunsplit(href._replace(path=''))
        for k, v in element.attrib.items():
            print(k, v)

    # incorporate_into_defs
    try:
        defs = find_first(root, 'defs')
    except IndexError:
        defs = etree.Element('defs')
        find_first(root, 'svg').insert(0, defs)
    # FIXME: These def elements won't necessarily refer to _their_ dependencies
    # correctly!
    defs.extend(to_add_to_def)
    return tree


def write_file(path, src_dir, dest_dir, tree):
    rel_path = os.path.relpath(path, src_dir)
    dest_path = os.path.abspath(os.path.join(dest_dir, rel_path))
    with open_with_dirs(dest_path, 'wb') as f:
        tree.write(
            f, pretty_print=True, xml_declaration=True, encoding='utf-8')


def main(
        src_dir: 'The directory containing svg element definitions',
        dest_dir: 'The directory to which to write output files',
        *to_build: 'The svg files referencing definitions from source files'):
    '''
    Takes a bunch of svg files containing element definitions with id
    attributes, and a bunch of files to build referencing those definitions,
    and produces output svg files with the external elements inlined.
    '''
    ensure_dir(src_dir, 'src_dir')
    ensure_dir(dest_dir, 'dest_dir')
    elements_by_url = load_all_elements(file_paths_under(src_dir))
    g = generate_dependency_graph(elements_by_url)
    for filepath in to_build:
        tree = build_file(filepath, elements_by_url, g)
        write_file(filepath, src_dir, dest_dir, tree)


if __name__ == '__main__':
    argh.dispatch_command(main)
