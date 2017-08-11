#!/usr/bin/env python3

import os
import errno
import sys
import re
from hashlib import sha1
from collections import MutableMapping
from itertools import chain
from urllib.parse import urlsplit, urlunsplit, SplitResult

from lxml import etree
import networkx

url_re = re.compile('url\((.*)\)')
url_str = lambda u: 'url({})'.format(u)


class Resource:
    __slots__ = (
        'guid', 'root_path', 'file_path', 'elem', 'orig_id', 'orig_hrefs',
        'children', 'elem_attrs')

    def __init__(self, guid, root_path, file_path, elem, children):
        self.guid = guid
        self.root_path = root_path
        self.file_path = file_path
        self.elem = elem
        self.elem_attrs = NamespacePreservingMap(elem)
        self.orig_id = self.elem_attrs.get('id')
        if self.orig_id:
            self.elem_attrs['id'] = self.output_id
        self.orig_hrefs = self._canonicalise_and_extract_hrefs()
        self.children = children

    @property
    def tag(self):
        return etree.QName(self.elem).localname

    @property
    def output_id(self):
        if self.orig_id:
            return '{}_{}'.format(self.orig_id, self.guid)
        else:
            raise TypeError(
                '{!r} has no given id in the original xml'.format(self))

    def _canonicalise_and_extract_hrefs(self):
        '''
        Yields the URLs referenced by attributes of this resource's element,
        canonicalising the path with respect to the root path so as to make
        urls across different resource objects directly comparable.
        '''
        return self.rewrite_hrefs(self._canonicalise_href)

    def _canonicalise_href(self, href):
        if href.netloc:
            return href
        else:
            if href.path:
                href_path = os.path.relpath(
                    os.path.realpath(os.path.join(self.root_path, href.path)),
                    self.root_path)
                return href._replace(path=href_path)
            else:
                return href._replace(path=self.file_path)

    def rewrite_hrefs(self, f):
        '''
        Rewrites the elements reference URLs to point at global ids of elements
        assumed to be included in the local file, rather than using a file:id
        pair.
        '''
        return frozenset(self._rewrite_hrefs(f))

    def _rewrite_hrefs(self, f):
        old_href = self.elem_attrs.get('href')
        if old_href is not None:
            new_href = f(urlsplit(old_href))
            self.elem_attrs['href'] = urlunsplit(new_href)
            yield new_href
        for name, value in self.elem_attrs.items():
            match = url_re.match(value)
            if match:
                new_href = f(urlsplit(match.group(1)))
                self.elem_attrs[name] = url_str(urlunsplit(new_href))
                yield new_href

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def __repr__(self):
        return '<{} {}{}>'.format(
            self.tag, self.guid,
            ' id="{}"'.format(self.orig_id) if self.orig_id else '')


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


def generate_guid(file_path, tag, parent_guid, idx):
    return sha1(
        bytes(file_path + tag + parent_guid + str(idx), encoding='utf-8')
    ).hexdigest()[:6]


def generate_resource(root_path, file_path, elem, parent_guid='', idx=0):
    assert not isinstance(elem, etree._Comment)
    guid = generate_guid(file_path, elem.tag, parent_guid, idx)
    children = tuple(
        generate_resource(
            root_path, file_path, child_elem, parent_guid=guid, idx=i)
        for i, child_elem in enumerate(elem.iterchildren())
        if not isinstance(child_elem, etree._Comment))
    return Resource(guid, root_path, file_path, elem, children)


def build_element_graph(resources):
    g = networkx.DiGraph(name='element_graph')
    g.add_nodes_from(resources)
    for r in resources:
        for c in r.children:
            g.add_edge(r, c)
    return g


def build_link_graph(resources):
    resources_by_url = {
        SplitResult('', '', r.file_path, '', r.orig_id): r for r in resources
        if r.orig_id
    }
    g = networkx.DiGraph()
    g.add_nodes_from(resources)
    for r in resources:
        for dep_url in r.orig_hrefs:
            try:
                g.add_edge(r, resources_by_url[dep_url])
            except KeyError:
                print(
                    '{} referenced unknown resource {}'.format(
                        r.file_path, urlunsplit(dep_url)),
                    file=sys.stderr)
    return g, resources_by_url


def normalise_link(url, output_ids_by_url):
    if url.netloc:
        # Don't normalise external links
        # FIXME: this is repetition from inbound link canonicalisation
        return url
    else:
        return SplitResult('', '', '', '', output_ids_by_url[url])


def normalise_links(resources, resources_by_url):
    '''
    Makes all the links of the given resources point to a globalised id in the
    SVG's own file, so that once we've included all the externally referenced
    XML everything will line up.
    '''
    output_ids_by_url = {
        url: r.output_id for url, r in resources_by_url.items()}
    for r in resources:
        r.rewrite_hrefs(lambda url: normalise_link(url, output_ids_by_url))


def ensure_dir(path, hint=''):
    if not os.path.isdir(path):
        if hint:
            hint += ': '
        raise TypeError('{}{} is not a directory'.format(hint, path))


def makedirs(path):
    try:
        os.makedirs(path)
    except IOError as e:
        if e.errno != errno.EEXIST:
            raise


def open_with_dirs(file_path, mode):
    makedirs(os.path.dirname(file_path))
    return open(file_path, mode)


def add_defs(root_resource, dependency_roots):
    for r in root_resource.walk():
        if r.tag == 'defs':
            defs_elem = r.elem
            break
    else:
        defs_elem = etree.Element('defs')
        root_resource.elem.insert(0, defs_elem)
    for dep_resource in dependency_roots:
        defs_elem.append(dep_resource.elem)


def write_file(orig_path, src_dir, dest_dir, tree):
    rel_path = os.path.relpath(orig_path, src_dir)
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
    trees_by_file_path = load_all_trees(src_dir)
    resources_by_tree = extract_resources(src_dir, trees_by_file_path)
    all_resources = tuple(
        chain(*(r.walk() for r in resources_by_tree.values())))
    element_graph = build_element_graph(all_resources)
    link_graph, resources_by_url = build_link_graph(all_resources)
    full_dep_graph = networkx.compose(element_graph, link_graph)
    normalise_links(all_resources, resources_by_url)
    for file_path in to_build:
        tree = trees_by_file_path[file_path]
        root_resource = resources_by_tree[tree]
        tree_resources = networkx.descendants(element_graph, root_resource)
        tree_and_ext_resources = networkx.descendants(
            full_dep_graph, root_resource)
        ext_resources_graph = element_graph.subgraph(
            tree_and_ext_resources - tree_resources)
        ext_root_resources = {
            n for n in ext_resources_graph.nodes() if not
            networkx.ancestors(ext_resources_graph, n)}
        add_defs(root_resource, ext_root_resources)
        write_file(file_path, src_dir, dest_dir, tree)


if __name__ == '__main__':
    import argh
    argh.dispatch_command(main)
