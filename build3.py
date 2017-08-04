#!/usr/bin/env python3

import os
import sys
import re
from hashlib import sha1
from collections import MutableMapping
from itertools import chain
from urllib.parse import urlsplit, urlunsplit, SplitResult

from lxml import etree
import networkx

url_re = re.compile('url\((.*)\)')


class Resource:
    __slots__ = (
        'gid', 'root_path', 'file_path', 'elem', 'id_', 'children',
        'elem_attrs')

    def __init__(self, gid, root_path, file_path, elem, children):
        self.gid = gid
        self.root_path = root_path
        self.file_path = file_path
        self.elem = elem
        self.elem_attrs = NamespacePreservingMap(elem)
        self.id_ = self.elem_attrs.get('id')
        if self.id_:
            self.elem_attrs['id'] = gid
        self.children = children

    @property
    def hrefs(self):
        return map(self._canonicalise_href, self._extract_hrefs())

    def _extract_hrefs(self):
        for name, value in self.elem_attrs.items():
            if name == 'href':
                yield urlsplit(value)
            else:
                match = url_re.match(value)
                if match:
                    yield urlsplit(match.group(1))

    def _canonicalise_href(self, href):
        if href.path:
            href_path = os.path.relpath(
                os.path.realpath(os.path.join(self.root_path, href.path)),
                self.root_path)
            return href._replace(path=href_path)
        else:
            return href._replace(path=self.file_path)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def __repr__(self):
        return '<{} {}{}>'.format(
            etree.QName(self.elem).localname,
            self.gid[:6],
            ' id="{}"'.format(self.id_) if self.id_ else '')


class NamespacePreservingMap(MutableMapping):
    '''
    lxml's element.attrib dict doesn't make handling element attributes with
    namespaces at all easy. This abstraction tries to make it easier to deal
    with that.

    NB. this won't handle tags with the same name from different namespaces
    '''

    def __init__(self, element):
        self._element = element
        self._keymap = {etree.QName(k).localname: k for k in element.attrib}

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


def file_paths_under(root_path):
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def load_all_trees(src_path):
    return {
        # FIXME: handle non-xml files in src path
        file_path: etree.parse(file_path) for file_path in
        file_paths_under(src_path)
    }


def extract_resources(root_path, trees):
    return {
        tree: generate_resource(
            root_path,
            os.path.relpath(file_path, root_path),
            tree.getroot())
        for file_path, tree in trees.items()
    }


def generate_gid(file_path, tag, parent_gid, idx):
    return sha1(
        bytes(file_path + tag + parent_gid + str(idx), encoding='utf-8')
    ).hexdigest()


def generate_resource(root_path, file_path, elem, parent_gid='', idx=0):
    assert not isinstance(elem, etree._Comment)
    gid = generate_gid(file_path, elem.tag, parent_gid, idx)
    children = tuple(
        generate_resource(
            root_path, file_path, child_elem, parent_gid=gid, idx=i)
        for i, child_elem in enumerate(elem.iterchildren())
        if not isinstance(child_elem, etree._Comment))
    return Resource(gid, root_path, file_path, elem, children)


def build_element_graph(resources):
    g = networkx.DiGraph(name='element_graph')
    g.add_nodes_from(resources)
    for r in resources:
        for c in r.children:
            g.add_edge(r, c)
    return g


def build_link_graph(resources):
    resources_by_url = {
        SplitResult('', '', r.file_path, '', r.id_): r for r in resources
        if r.id_
    }
    g = networkx.DiGraph()
    g.add_nodes_from(resources)
    for r in resources:
        for dep_url in r.hrefs:
            try:
                g.add_edge(r, resources_by_url[dep_url])
            except KeyError:
                print(
                    '{} referenced unknown resource {}'.format(
                        r.file_path, urlunsplit(dep_url)),
                    file=sys.stderr)
    return g, resources_by_url


def ensure_dir(path, hint=''):
    if not os.path.isdir(path):
        if hint:
            hint += ': '
        raise TypeError('{}{} is not a directory'.format(hint, path))


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
    trees_by_file_path = load_all_trees(src_dir)
    resources_by_tree = extract_resources(src_dir, trees_by_file_path)
    all_resources = tuple(
        chain(*(r.walk() for r in resources_by_tree.values())))
    element_graph = build_element_graph(all_resources)
    link_graph, resources_by_url = build_link_graph(all_resources)
    full_dep_graph = networkx.compose(element_graph, link_graph)
    for file_path in to_build:
        tree = trees_by_file_path[file_path]
        root_resource = resources_by_tree[tree]
        file_resources = networkx.descendants(element_graph, root_resource)
        link_resources = networkx.descendants(link_graph, root_resource)
        full_dep_resources = networkx.descendants(full_dep_graph, root_resource)
        # dependencies = networkx.ancestors(element_graph, root_resource)
        # dependencies = set(r for r in dependencies if r.id_)
        print(file_resources)
        print(full_dep_resources - file_resources)


if __name__ == '__main__':
    import argh
    argh.dispatch_command(main)
