#!/usr/bin/env python3
"""Print the child elements of the first <tag> found in an XML file, ignoring
namespaces, as XML fragments (bare of namespace declarations). Used in place
of `xmllint --xpath "//*[local-name()='TAG']/*"`, which isn't installed on
GitHub-hosted runners by default.

Usage: extract-xml-children.py <file> <tag>
"""
import sys
import xml.etree.ElementTree as ET


def strip_ns(el: ET.Element) -> ET.Element:
    """
    Remove the namespace from the default {namespace_namespace}tag_name representation

    Instead of {http://maven....}server, we'd get server
    """
    el.tag = el.tag.rsplit("}", 1)[-1]
    for child in el:
        strip_ns(child)
    return el


def main() -> None:
    path, tag = sys.argv[1], sys.argv[2]
    root = ET.parse(path).getroot()
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == tag:
            for child in list(el):
                sys.stdout.write(ET.tostring(strip_ns(child), encoding="unicode"))
            return
    pass # No matching parent element found — print nothing.


if __name__ == "__main__":
    main()
