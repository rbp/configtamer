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
    config               = empty_lines? top_level? sections?

    top_level            = (assignment newline lines) / assignment
    lines                = (line newline lines) / line
    line                 = assignment / empty_line

    sections             = (section newline sections) / section
    section              = section_header newline indented_assignments
    section_header       = section_name whitespace_inline* assignment_colon whitespace_inline*
    section_name         = key
    indented_assignments = (indented_assignment newline indented_assignments) / indented_assignment
    indented_assignment  = " "+ assignment

    assignment           = key whitespace_inline* assignment_op whitespace_inline* value whitespace_inline*
    key                  = ~"[a-z0-9][a-z0-9_]*"i
    assignment_colon     = ":"
    assignment_equals    = "="
    assignment_op        = assignment_colon / assignment_equals
    # This seems a little too permissive, but we'll get to that.
    value                = ~"[^\s]([^\r\n]*[^\s])?"
    empty_lines          = (empty_line newline empty_lines) / (empty_line newline)
    empty_line           = whitespace_inline*
    whiltespace_line     = whitespace_inline+
    whitespace_inline    = " " / "\t"
    newline              = "\r\n" / "\n" / "\r"
    whitespace           = whitespace_inline / newline
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
        # each of visited_children can be:
        # - a list of {key: "key", value: "value"} dicts
        #   representing assignments and sections (or None, representing empty matches)
        # - "None", representing empty matches
        assignments = flatten(visited_children)
        return assignments

    def visit_top_level(self, node, visited_children):
        # visited_children is a list of {key: "key", value: "value"} dicts
        # representing assignments and sections
        # (and "None" children representing whitespace)
        assignments = visited_children
        return assignments

    def visit_lines(self, node, visited_children):
        # visited_children is a list of {key: "key", value: "value"} dicts
        # representing assignments and sections
        # (and "None" children representing whitespace)
        assignments = visited_children
        return assignments

    def visit_line(self, node, visited_children):
        # visited_children is a single-element list
        # of a dict {key: "key", value: "value"} representing assignments
        # (or "None" children representing an empty line)
        assert len(visited_children) == 1, "Expected only one child in a line: {}".format(visited_children)
        return visited_children

    def visit_assignment(self, node, visited_children):
        merged = dict(sum([c.items() for c in
                           flatten(visited_children)], []))
        return merged

    def visit_key(self, node, visited_children):
        return {'key': node.text}

    def visit_value(self, node, visited_children):
        return {'value': node.text}

    def visit_empty_line(self, node, visited_children):
        return visited_children
        
    def visit_assignment_colon(self, node, visited_children):
        return visited_children

    def visit_whitespace_inline(self, node, visited_children):
        return visited_children

    def visit_newline(self, node, visited_children):
        return visited_children

    # If we're not interested in this node, flatten it as much as possible
    def generic_visit(self, node, visited_children):
        return visited_children

    # If we're not interested in this node, we just bubble up non-None children,
    # or None if this is a leaf.
    def generic_visit(self, node, visited_children):
        valuable_children = [c for c in visited_children if c is not None]
        if valuable_children:
            return valuable_children
        return None


def parse(config_string):
    try:
        parsed_config = grammar.parse(config_string)
    except parsimonious.exceptions.IncompleteParseError as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        raise SyntaxError, "Invalid config file syntax: {}".format(exc_value), exc_traceback

    visitor = TheCPANodeVisitor()
    assignments = visitor.visit(parsed_config)

    config = process_assignments(assignments)
    return config


def process_assignments(assignments):
    items = {}
    to_interpolate = {}

    import re
    re_interpolation = re.compile(r'\{([^}]+)\}')

    for assignment in assignments:
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
