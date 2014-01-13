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
    config               = block*
    block                = section / assignment / empty_line
    section              = section_header indented_assignment
    section_header       = section_name whitespace_inline* ":" whitespace_inline* newline
    section_name         = key
    indented_assignment  = "    " assignment
    assignment           = key whitespace_inline* assignment_op whitespace_inline* value whitespace?
    key                  = ~"[a-z0-9][a-z0-9_]*"i
    assignment_colon     = ":"
    assignment_equals    = "="
    assignment_op        = assignment_colon / assignment_equals
    # This seems a little too permissive, but we'll get to that.
    value                = ~"[^\s](.*[^\s])?"
    # This is not entirely correct. It's either whitespace* + newline, or whitespace+ + EOF.
    empty_line           = (whitespace_inline* newline) / (whitespace_inline+ !key)
    whitespace_inline    = " " / "\t"
    newline              = "\n" / "\r\n" / "\r"
    whitespace           = whitespace_inline / newline
    """)


class TheCPANodeVisitor(NodeVisitor):
    def visit_config(self, node, visited_children):
        # By this point, we have a list of {key: "key", value: "value"} dicts
        # representing assignments (and "None" children representing whitespace)
        assignments = [c for c in visited_children if c is not None]
        return assignments

    def visit_block(self, node, visited_children):
        # "children" can be either: a section; a single assignment; or None (for an empty line)
        if visited_children is not None:
            assert len(visited_children) == 1
            return visited_children[0]
        return None

    def visit_section(self, node, visited_children):
        section_name = visited_children[0]
        assignments =  [c for c in visited_children[1] if c is not None]
        section =  {'key': section_name,
                    'value': assignments}
        return section

    def visit_section_header(self, node, visited_children):
        section_name = visited_children[0]["key"]
        return section_name

    def visit_assignment(self, node, visited_children):
        merged = dict(sum([c.items() for c in visited_children if c is not None], []))
        return merged

    def visit_key(self, node, visited_children):
        return {'key': node.text}

    def visit_value(self, node, visited_children):
        return {'value': node.text}

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
