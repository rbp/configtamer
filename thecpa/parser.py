#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from .config import Config


grammar = Grammar(
    r"""
    config              = line*
    line                = assignment / empty_line
    assignment          = key whitespace_inline* assignment_op whitespace_inline* value whitespace?
    key                 = ~"[a-z0-9][a-z0-9_]*"i
    assignment_op       = ":" / "="
    # This seems a little too permissive, but we'll get to that.
    value               = ~"[^\s](.*[^\s])?"
    empty_line          = (whitespace_inline* newline) / whitespace_inline+
    whitespace_inline   = " " / "\t"
    newline             = "\n" / "\r\n" / "\r"
    whitespace          = whitespace_inline / newline
    """)


class TheCPANodeVisitor(NodeVisitor):
    def visit_config(self, node, visited_children):
        # By this point, we have a list of {key: "key", value: "value"} dicts
        # representing assignments (and "None" children representing whitespace)
        assignments = [c for c in visited_children if c is not None]
        return assignments

    def visit_line(self, node, visited_children):
        # "Children" is either a single assignment, or None (for an empty line)
        if visited_children is not None:
            assert len(visited_children) == 1
            return visited_children[0]
        return None

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
    config = Config()
    items = {}
    to_interpolate = {}

    import re
    re_interpolation = re.compile(r'\{([^}]+)\}')

    parsed_config = grammar.parse(config_string)
    visitor = TheCPANodeVisitor()
    assignments = visitor.visit(parsed_config)

    for assignment in assignments:
        key = assignment["key"]
        value = assignment["value"]

        if re_interpolation.search(value):
            to_interpolate[key] = value
            continue

        items[key] = value

    for key, value in to_interpolate.items():
        value = re_interpolation.sub(lambda m: items[m.group(1)], value)
        items[key] = value
    
    for key, value in items.items():
        config.__add_key_value__(key, value)

    return config
