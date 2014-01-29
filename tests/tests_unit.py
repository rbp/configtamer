#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import unittest
import configtamer


class TestParser(unittest.TestCase):
    def try_parse(self, config_string, expected):
        """Parses config_string and checks it against the expected result.
        Expected is a dict-of-dicts.
        """
        parsed = configtamer.parse(config_string)
        self.validate_parsed_config(parsed, expected)

    def validate_parsed_config(self, parsed, expected):
        # All keys and attributes should match
        # TODO: do this for every level of nested sections
        assert set(parsed) == set(expected), "Expected: {}.\nGot: {}".format(set(expected), set(parsed))
        assert parsed.__dict__ == expected, "Expected: {}.\nGot: {}".format(expected, parsed.__dict__)

        for key in expected:
            # Config values should be identically accessible as attributes or dict keys
            assert parsed.get(key) == expected[key], "parsed[{}] != {}".format(key, expected[key])
            assert getattr(parsed, key) == expected[key], "parsed.{} != {}".format(key, expected[key])

            # Config keys should be case-insensitive
            assert parsed.get(key) == parsed.get(key.swapcase()) == parsed.get(key.title()), \
                   "Key {} should be case-insensitive!".format(key)
            assert getattr(parsed, key) == getattr(parsed, key.swapcase()) == getattr(parsed, key.title()), \
                                      "Attribute {} should be case-insensitive!".format(key)

            if isinstance(expected[key], dict):
                # Let's recurse into sections
                self.validate_parsed_config(parsed[key], expected[key])


class TestSimpleParser(TestParser):
    def test_empty_string(self):
        self.try_parse("", {})

    def test_whitespace_only_string(self):
        self.try_parse(" \t\n", {})

    def test_empty_lines(self):
        self.try_parse("\n\n\n", {})

    def test_single_key_value_pair(self):
        self.try_parse("foo: bar",
                       {'foo': 'bar'})

    def test_two_key_value_pairs(self):
        self.try_parse("""
parrot: dead
slug: mute
""",
                       {"parrot": "dead", "slug": "mute"})

    def test_keys_are_case_insensitive(self):
        self.try_parse("Parrot: dead", {"parrot": "dead"})

    def test_values_with_whitespace(self):
        self.try_parse("""
parrot: is no more
it: has\tceased\tto\tbe
it_has: expired\tand gone\tmeet its\tmaker
""",
                       {"parrot": "is no more",
                        "it": "has\tceased\tto\tbe",
                        "it_has": "expired\tand gone\tmeet its\tmaker"})

    def test_values_with_leading_and_trailing_whitespace(self):
        self.try_parse("""
customer: 'ello Miss    \t
clerk:    what do you mean, miss?  \t
customer_again:    I'm sorry, I have a cold.    \t\t
""",
                       {"customer": "'ello Miss",
                        "clerk": "what do you mean, miss?",
                        "customer_again": "I'm sorry, I have a cold."})

    def test_assignments_with_interspersed_whitespace(self):
        self.try_parse("""

customer: 'ello Miss
    
clerk: what do you mean, miss?
\t

customer_again: I'm sorry, I have a cold.
\t  \t


""",
                       {"customer": "'ello Miss",
                        "clerk": "what do you mean, miss?",
                        "customer_again": "I'm sorry, I have a cold."})

    def test_top_level_assignment_with_leading_whitespace_in_key(self):
        self.assertRaises(SyntaxError, configtamer.parse, "    parrot: is no more")


class TestInterpolation(TestParser):
    def test_simple_interpolation(self):
        self.try_parse("""
pet: parrot
this_is: a dead {pet}
        """,
                       {"pet": "parrot",
                        "this_is": "a dead parrot"})

    def test_interpolate_same_key_twice(self):
        self.try_parse("""
parrot: Polly
wakeup_call: {parrot}, wake up! {parrot}!
        """,
                       {'parrot': 'Polly',
                        'wakeup_call': 'Polly, wake up! Polly!'})

    def test_interpolate_key_before_assignment(self):
        self.try_parse("""
wakeup_call: {parrot}, wake up! {parrot}!
parrot: Polly
        """,
                       {'parrot': 'Polly',
                        'wakeup_call': 'Polly, wake up! Polly!'})

    def test_interpolate_different_keys_into_same_value(self):
        self.try_parse("""
parrot: Polly
wakeup_call: {parrot} parrot, wake up! This is your {hour} o'clock alarm call!
hour: 9
        """,
                       {'parrot': 'Polly',
                        'wakeup_call': "Polly parrot, wake up! This is your 9 o'clock alarm call!",
                        'hour': '9'})

    def test_interpolate_values_with_whitespace(self):
        self.try_parse("""
shopkeeper: It's {dead}!
Mr_Praline: {dead}??
dead: pining for the fjords
        """,
                       {"shopkeeper": "It's pining for the fjords!",
                        "mr_praline": "pining for the fjords??",
                        "dead": "pining for the fjords"})

    def test_interpolate_values_with_leading_and_trailing_whitespace(self):
        self.try_parse("""
shopkeeper: \t  It's {dead}!  
Mr_Praline: {dead}??   \t
dead:   \t  pining for the fjords
        """,
                       {"shopkeeper": "It's pining for the fjords!",
                        "mr_praline": "pining for the fjords??",
                        "dead": "pining for the fjords"})


class TestSections(TestParser):
    def test_section_with_one_assignment(self):
        self.try_parse("""
parrot:
    complaint: it is dead
        """,
                       {'parrot':
                        {'complaint': 'it is dead'}})
        #assert set(parsed) == set(["parrot"])
        #assert set(parsed.parrot) == set(["complaint"])
        #assert parsed.parrot.complaint == 'it is dead'

    def test_section_with_two_assignments(self):
        self.try_parse("""
parrot:
    complaint: it is dead
    hypothesis: it's pining
        """,
                       {'parrot':
                        {'complaint': 'it is dead',
                         'hypothesis': "it's pining"}})

    def test_section_with_two_assignments_with_empty_line(self):
        self.try_parse("""
parrot:
    complaint: it is dead

    hypothesis: it's pining
        """,
                       {'parrot':
                        {'complaint': 'it is dead',
                         'hypothesis': "it's pining"}})

    def test_section_with_three_assignments_and_empty_lines(self):
        self.try_parse("""
parrot:
    complaint: it is dead

    hypothesis: it's pining

    retort: it's not pining, it's passed on!
        """,
                       {'parrot':
                        {'complaint': 'it is dead',
                         'hypothesis': "it's pining",
                         'retort': "it's not pining, it's passed on!"}})


class TestTopLevelAndSections(TestParser):
    def test_one_top_level_assignment_one_section(self):
        self.try_parse("""
where: pet shop
parrot:
    complaint: it is dead
        """,
                       {"where": "pet shop",
                        "parrot":
                        {"complaint": "it is dead"}})

    def test_several_top_level_one_section_with_several_assignments(self):
        self.try_parse("""
Where: pet shop
Customer: Mr. Praline
parrot:
    complaint: it is dead
    hypothesis: it's pining
    retort: it's not pining, it's passed on!
        """,
                       {'where': 'pet shop',
                        'customer': 'Mr. Praline',
                        'parrot':
                        {'complaint': 'it is dead',
                         'hypothesis': "it's pining",
                         'retort': "it's not pining, it's passed on!"}})

    def test_several_top_level_one_section_with_several_assignments_and_empty_lines(self):
        self.try_parse("""

Where: pet shop

     \t
Customer: Mr. Praline

  \t  

parrot:

    complaint: it is dead\t


    hypothesis: it's pining
    retort: it's not pining, it's passed on!

   \t      """,
                       {'where': 'pet shop',
                        'customer': 'Mr. Praline',
                        'parrot':
                        {'complaint': 'it is dead',
                         'hypothesis': "it's pining",
                         'retort': "it's not pining, it's passed on!"}})

    def test_two_sections(self):
        self.try_parse("""
parrot:
    Colour: blue
    Talks: True
    State: Dead
slug:
    Colour: who knows?
    Talks: False
    State: Alive""",
                       {"parrot":
                        {"colour": "blue",
                         "talks": "True",
                         "state": "Dead"},
                        "slug":
                        {"colour": "who knows?",
                         "talks": "False",
                         "state": "Alive"}})

    def test_two_sections_with_empty_lines(self):
        self.try_parse("""

parrot:
 \t
    Colour: blue


    Talks: True
    State: Dead

  \t



slug:


    Colour: who knows?  \t
\t
    Talks: False

    State: Alive
    \t

    
""",
                       {"parrot":
                        {"colour": "blue",
                         "talks": "True",
                         "state": "Dead"},
                        "slug":
                        {"colour": "who knows?",
                         "talks": "False",
                         "state": "Alive"}})

    def test_three_sections(self):
        self.try_parse("""
parrot:
    Colour: blue
    Talks: True
    State: Dead

slug:
    Colour: who knows?
    Talks: False
    State: Alive

shopkeeper:
    Colour: white
    Talks: A lot
    State: Alive but confused
""",
                       {"parrot":
                        {"colour": "blue",
                         "talks": "True",
                         "state": "Dead"},
                        "slug":
                        {"colour": "who knows?",
                         "talks": "False",
                         "state": "Alive"},
                        "shopkeeper":
                        {"colour": "white",
                         "talks": "A lot",
                         "state": "Alive but confused"}})

    def test_several_top_level_several_sections(self):
        self.try_parse("""
Where: pet shop

Customer: Mr. Praline
Time: Lunch time

parrot:
    Colour: blue
    Talks: True
    State: Dead

slug:
    Colour: who knows?
    Talks: False
    State: Alive

shopkeeper:
    Colour: white
    Talks: A lot
    State: Alive but confused""",
                       {'where': 'pet shop',
                        'customer': 'Mr. Praline',
                        'time': 'Lunch time',
                        "parrot":
                        {"colour": "blue",
                         "talks": "True",
                         "state": "Dead"},
                        "slug":
                        {"colour": "who knows?",
                         "talks": "False",
                         "state": "Alive"},
                        "shopkeeper":
                        {"colour": "white",
                         "talks": "A lot",
                         "state": "Alive but confused"}})

    def test_top_level_after_section(self):
        self.assertRaises(SyntaxError, configtamer.parse, """
Where: pet shop
parrot:
    is: no more

Customer: Mr. Praline""")


class TestInterpolationInSection(TestParser):
    def test_simple_interpolation(self):
        self.try_parse("""
problem:
    pet: parrot
    this_is: a dead {pet}
        """,
                       {'problem':
                        {"pet": "parrot",
                         "this_is": "a dead parrot"}})

    def test_interpolate_same_key_twice(self):
        self.try_parse("""
try_and_wake_him_up:
    parrot: Polly
    wakeup_call: {parrot}, wake up! {parrot}!
        """,
                       {'try_and_wake_him_up':
                        {'parrot': 'Polly',
                         'wakeup_call': 'Polly, wake up! Polly!'}})

    def test_interpolate_key_before_assignment(self):
        self.try_parse("""
try_and_wake_him_up:
    wakeup_call: {parrot}, wake up! {parrot}!
    parrot: Polly
        """,
                       {'try_and_wake_him_up':
                        {'parrot': 'Polly',
                         'wakeup_call': 'Polly, wake up! Polly!'}})

    def test_interpolate_different_keys_into_same_value(self):
        self.try_parse("""
try_and_wake_him_up:
    parrot: Polly
    wakeup_call: {parrot} parrot, wake up! This is your {hour} o'clock alarm call!
    hour: 9
        """,
                       {'try_and_wake_him_up':
                        {'parrot': 'Polly',
                         'wakeup_call': "Polly parrot, wake up! This is your 9 o'clock alarm call!",
                         'hour': '9'}})

    def test_interpolate_values_with_whitespace(self):
        self.try_parse("""
excuse:
    shopkeeper: It's {dead}!
    Mr_Praline: {dead}??
    dead: pining for the fjords
        """,
                       {'excuse':
                        {"shopkeeper": "It's pining for the fjords!",
                         "mr_praline": "pining for the fjords??",
                         "dead": "pining for the fjords"}})

    def test_interpolate_values_with_leading_and_trailing_whitespace(self):
        self.try_parse("""
excuse:
    shopkeeper: \t  It's {dead}!  
    Mr_Praline: {dead}??   \t
    dead:   \t  pining for the fjords
        """,
                       {'excuse':
                        {"shopkeeper": "It's pining for the fjords!",
                         "mr_praline": "pining for the fjords??",
                         "dead": "pining for the fjords"}})

    def test_interpolate_in_two_sections(self):
        self.try_parse("""
parrot:
    Colour: blue
    Breed: Norwegian {Colour}

slug:
    Colour: slimy brown
    Breed: Gooey {Colour}
    """,
                       {'parrot':
                        {'colour': 'blue',
                         'breed': 'Norwegian blue'},
                        'slug':
                        {'colour': 'slimy brown',
                         'breed': 'Gooey slimy brown'}})
        


class TestFlatten(unittest.TestCase):
    def test_None(self):
        assert configtamer.parser.flatten(None) == [None]
    def test_empty_list(self):
        assert configtamer.parser.flatten([]) == []
    def test_list_of_empty_list(self):
        assert configtamer.parser.flatten([[]]) == []
    def test_list_of_None(self):
        assert configtamer.parser.flatten([None]) == []
    def test_list_single_element(self):
        assert configtamer.parser.flatten(['foo']) == ['foo']
    def test_list_of_list_of_single_element(self):
        assert configtamer.parser.flatten([['foo']]) == ['foo']
