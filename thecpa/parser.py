#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import sys

import parsimonious
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from .config import Config


grammar = Grammar(
    r"""
    config               = empty_lines? top_level? sections? (newline trailing_empty_lines)?

    top_level            = (assignment newline lines) / assignment
    lines                = (line newline lines) / line
    line                 = assignment / empty_line

    sections             = (section newline sections) / section
    section              = section_header newline empty_lines? indented_assignments
    section_header       = section_name whitespace_inline* assignment_colon whitespace_inline*
    section_name         = key
    indented_assignments = (indented_assignment newline indented_lines) / indented_assignment
    indented_lines       = (indented_line newline indented_lines) / indented_line
    indented_line        = indented_assignment / empty_line
    indented_assignment  = " "+ assignment

    assignment           = key whitespace_inline* assignment_op whitespace_inline* value whitespace_inline*
    key                  = ~"[a-z0-9][a-z0-9_]*"i
    # This seems a little too permissive, but we'll get to that.
    value                = ~"[^\s]([^\r\n]*[^\s])?"
    assignment_colon     = ":"
    assignment_equals    = "="
    assignment_op        = assignment_colon / assignment_equals
    empty_lines          = (empty_line newline empty_lines) / (empty_line newline)
    trailing_empty_lines = (empty_line newline empty_lines) / empty_line
    empty_line           = whitespace_inline*
    whitespace_inline    = " " / "\t"
    newline              = "\r\n" / "\n" / "\r"
    """)


def flatten(items):
    "Flattens the items list. Removes None values"
    if not isinstance(items, (list, tuple)):
        return [items]

    flat = [i for sublist in items
            for i in flatten(sublist)
            if i is not None]
    return flat


class TheCPANodeVisitor(NodeVisitor):
    def visit_config(self, node, visited_children):
        # each of visited_children is a >=0 list of
        # {key: "key", value: "value"} or
        # {'name': "section_name", "assignments": [...]}
        # dicts representing assignments and sections (or None, representing empty matches)
        assignments = flatten(visited_children)
        return assignments

    def visit_line(self, node, visited_children):
        # visited_children is a list with either a single element,
        # a dict {key: "key", value: "value"} representing assignments,
        # or an empty list representing an empty line.
        assert len(visited_children) == 1, "Expected only one child in a line: {}".format(visited_children)
        return visited_children

    def visit_assignment(self, node, visited_children):
        # After flattening, visited_children are one dict with "key"
        # and one with "value"
        merged = dict(sum([c.items() for c in
                           flatten(visited_children)], []))
        return merged

    def visit_section_header(self, node, visited_children):
        # visited_children, flattened, should contain a single element,
        # a {key: section_name} dict representing the section name
        dicts = flatten(visited_children)
        assert len(dicts) == 1, "Expected only one child on a section header: {}".format(dicts)
        section_name = dicts[0]["key"]
        return {"section": section_name}

    def visit_section(self, node, visited_children):
        """visited_children is a list including one {section: name} dict
        and 1 or more other dicts representing assignments."""
        dicts = flatten(visited_children)
        section = {'assignments': []}
        for d in dicts:
            if 'section' in d:
                section['name'] = d['section']
            else:
                section['assignments'].append(d)
        return section

    def visit_key(self, node, visited_children):
        return {'key': node.text}

    def visit_value(self, node, visited_children):
        return {'value': node.text}

    # If we're not interested in this node, just bubble it up.
    def generic_visit(self, node, visited_children):
        return visited_children


def parse(config_string):
    try:
        parsed_string = grammar.parse(config_string)
    except parsimonious.exceptions.IncompleteParseError as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        raise SyntaxError, "Invalid config file syntax: {}".format(exc_value), exc_traceback

    visitor = TheCPANodeVisitor()
    parsed_config = visitor.visit(parsed_string)

    config = process_config(parsed_config)
    return config


def process_config(config):
    """Processes a parsed config tree. Returns a Config object."""
    interpolated = process_assignments(config)
    for section in [d for d in config if 'name' in d]:
        setattr(interpolated, section['name'], process_assignments(d['assignments']))
    return interpolated


def process_assignments(config):
    """Handles interpolation of assignment values. Returns a Config object."""
    items = {}
    to_interpolate = {}

    import re
    re_interpolation = re.compile(r'\{([^}]+)\}')

    for item in config:
        if 'name' in item:
            # This is a section. Nothing to interpolate
            continue
        assignment = item
        key = assignment["key"]
        value = assignment["value"]

        # FIXME: better way of detecting a section :)
        if not isinstance(value, basestring):
            items[key] = process_assignments(value)
            continue

        if re_interpolation.search(value):
            to_interpolate[key] = value
            continue

        items[key] = value

    for key, value in to_interpolate.items():
        value = re_interpolation.sub(lambda m: items[m.group(1)], value)
        items[key] = value

    config = Config()
    for key, value in items.items():
        config.__add_key_value__(key, value)

    return config
