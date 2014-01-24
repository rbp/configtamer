#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import unittest
import thecpa


class TestSimpleParser(unittest.TestCase):
    def test_empty_string(self):
        parsed = thecpa.parse("")
        assert list(parsed) == []
        assert parsed.__dict__ == {}

    def test_whitespace_only_string(self):
        parsed = thecpa.parse(" \t\n")
        assert list(parsed) == []
        assert parsed.__dict__ == {}

    def test_empty_lines(self):
        parsed = thecpa.parse("\n\n\n")
        assert list(parsed) == []
        assert parsed.__dict__ == {}

    def test_single_key_value_pair(self):
        parsed = thecpa.parse("foo: bar")
        assert set(parsed) == set(["foo"])
        assert parsed.__dict__ == {'foo': 'bar'}
        assert parsed['foo'] == 'bar'
        assert parsed.foo == 'bar'

    def test_two_key_value_pairs(self):
        parsed = thecpa.parse("""
parrot: dead
slug: mute
""")
        assert set(parsed) == set(["parrot", "slug"])
        assert parsed.__dict__ == {"parrot": "dead", "slug": "mute"}
        assert parsed['parrot'] == parsed.parrot == 'dead'
        assert parsed['slug'] == parsed.slug == 'mute'

    def test_keys_are_case_insensitive(self):
        parsed = thecpa.parse("Parrot: dead")
        assert parsed.Parrot == "dead"
        assert parsed.parrot == "dead"

    def test_values_with_whitespace(self):
        parsed = thecpa.parse("""
parrot: is no more
it: has\tceased\tto\tbe
it_has: expired\tand gone\tmeet its\tmaker
""")
        assert parsed.parrot == "is no more"
        assert parsed.it == "\t".join(["has", "ceased", "to", "be"])
        assert parsed.it_has == "expired\tand gone\tmeet its\tmaker"

    def test_values_with_leading_and_trailing_whitespace(self):
        parsed = thecpa.parse("""
customer: 'ello Miss    \t
clerk:    what do you mean, miss?  \t
customer_again:    I'm sorry, I have a cold.    \t\t
""")
        assert parsed.customer == "'ello Miss"
        assert parsed.clerk == "what do you mean, miss?"
        assert parsed.customer_again == "I'm sorry, I have a cold."

    def test_assignments_with_interspersed_whitespace(self):
        parsed = thecpa.parse("""

customer: 'ello Miss
    
clerk: what do you mean, miss?
\t

customer_again: I'm sorry, I have a cold.
\t  \t


""")
        assert parsed.customer == "'ello Miss"
        assert parsed.clerk == "what do you mean, miss?"
        assert parsed.customer_again == "I'm sorry, I have a cold."

    def test_top_level_assignment_with_leading_whitespace_in_key(self):
        self.assertRaises(SyntaxError, thecpa.parse, "    parrot: is no more")


class TestInterpolation(unittest.TestCase):
    def test_simple_interpolation(self):
        parsed = thecpa.parse("""
pet: parrot
this_is: a dead {pet}
        """)
        assert parsed.pet == "parrot"
        assert parsed.this_is == "a dead parrot"

    def test_interpolate_same_key_twice(self):
        parsed = thecpa.parse("""
parrot: Polly
wakeup_call: {parrot}, wake up! {parrot}!
        """)
        assert parsed.wakeup_call == 'Polly, wake up! Polly!'

    def test_interpolate_key_before_assignment(self):
        parsed = thecpa.parse("""
wakeup_call: {parrot}, wake up! {parrot}!
parrot: Polly
        """)
        assert parsed.wakeup_call == 'Polly, wake up! Polly!'

    def test_interpolate_different_keys_into_same_value(self):
        parsed = thecpa.parse("""
parrot: Polly
wakeup_call: {parrot} parrot, wake up! This is your {hour} o'clock alarm call!
hour: 9
        """)
        assert parsed.wakeup_call == "Polly parrot, wake up! This is your 9 o'clock alarm call!"

    def test_interpolate_values_with_whitespace(self):
        parsed = thecpa.parse("""
shopkeeper: It's {dead}!
Mr_Praline: {dead}??
dead: pining for the fjords
        """)
        assert parsed.shopkeeper == "It's pining for the fjords!"
        assert parsed.mr_praline == "pining for the fjords??"

    def test_interpolate_values_with_leading_and_trailing_whitespace(self):
        parsed = thecpa.parse("""
shopkeeper: \t  It's {dead}!  
Mr_Praline: {dead}??   \t
dead:   \t  pining for the fjords
        """)
        assert parsed.shopkeeper == "It's pining for the fjords!"
        assert parsed.mr_praline == "pining for the fjords??"


class TestSections(unittest.TestCase):
    def test_section_with_one_assignment(self):
        parsed = thecpa.parse("""
parrot:
    complaint: it is dead
        """)
        assert set(parsed) == set(["parrot"])
        assert set(parsed.parrot) == set(["complaint"])
        assert parsed.parrot.complaint == 'it is dead'

    def test_section_with_two_assignments(self):
        parsed = thecpa.parse("""
parrot:
    complaint: it is dead
    hypothesis: it's pining
        """)
        assert set(parsed) == set(["parrot"])
        assert set(parsed.parrot) == set(["complaint", "hypothesis"])
        assert parsed.parrot.complaint == 'it is dead'

    def test_section_with_two_assignments_with_empty_line(self):
        parsed = thecpa.parse("""
parrot:
    complaint: it is dead

    hypothesis: it's pining
        """)
        assert set(parsed) == set(["parrot"])
        assert set(parsed.parrot) == set(["complaint", "hypothesis"])
        assert parsed.parrot.complaint == 'it is dead'

    def test_section_with_three_assignments_and_empty_lines(self):
        parsed = thecpa.parse("""
parrot:
    complaint: it is dead

    hypothesis: it's pining

    retort: it's not pining, it's passed on!
        """)
        assert set(parsed) == set(["parrot"])
        assert set(parsed.parrot) == set(["complaint", "hypothesis", "retort"])
        assert parsed.parrot.complaint == 'it is dead'
        assert parsed.parrot.retort == "it's not pining, it's passed on!"


class TestFlatten(unittest.TestCase):
    def test_None(self):
        assert thecpa.parser.flatten(None) == [None]
    def test_empty_list(self):
        assert thecpa.parser.flatten([]) == []
    def test_list_of_empty_list(self):
        assert thecpa.parser.flatten([[]]) == []
    def test_list_of_None(self):
        assert thecpa.parser.flatten([None]) == []
    def test_list_single_element(self):
        assert thecpa.parser.flatten(['foo']) == ['foo']
    def test_list_of_list_of_single_element(self):
        assert thecpa.parser.flatten([['foo']]) == ['foo']
