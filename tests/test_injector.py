#!/usr/bin/env python3

_license = """
blanket
Copyright 2025-2026 Larry Hastings
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import inspect
import sys
import unittest
import time
import threading
import tokenize

import blankettestlib
blankettestlib.preload_local_blanket()

from blanket import Location, inject_call
from blanket.injector import _find_statement_end

# Test decorators for version-specific tests
version_info = sys.version_info[0:2]
_python_3_8_plus  = sys.version_info >= (3,  8)
_python_3_11_plus = sys.version_info >= (3, 11)
_python_3_13_plus = sys.version_info >= (3, 13)

skip_if_no_column_info = unittest.skipUnless(_python_3_11_plus, "requires Python 3.11+ for column precision")
skip_if_column_info_is_available = unittest.skipIf(_python_3_11_plus, "requires Python 3.10- (no column info)")


def _strip_line_and_column_information(fn, *, firstlineno, name=None, qualname=None):
    """
    Remove line and column information from a function.  Supports Python 3.6-3.14.

    Pass an obviously invalid firstlineno value (like -1) to test corrupt code objects,
    or None to use the original function's co_firstlineno.
    """
    fn_type = type(fn)

    co = fn.__code__
    code_type = type(co)
    if firstlineno is None:
        firstlineno = co.co_firstlineno

    if name is not None:
        co_name = fn_name = name
    else:
        co_name = co.co_name
        fn_name = fn.__name__

    if _python_3_11_plus:
        if qualname is None:
            if name is not None:
                co_qualname = name
            else:
                co_qualname = co.co_qualname

    code_args = [
        co.co_argcount,
        co.co_kwonlyargcount,
        co.co_nlocals,
        co.co_stacksize,
        co.co_flags,
        co.co_code,
        co.co_consts,
        co.co_names,
        co.co_varnames,
        co.co_filename,
        co_name,
        firstlineno,
        b'', # lnotab in 3.6-3.9, linetable in 3.10+ -- either way, this is the line number information
        co.co_freevars,
        co.co_cellvars,
        ]

    if _python_3_8_plus:
        # added posonlyargcount, inconveniently as positional argument 1 (after argcount)
        code_args.insert(1, co.co_posonlyargcount)

    if _python_3_11_plus:
        # added qualname, inconveniently as positional argument 11 (after name)
        code_args.insert(11, co_qualname)
        # added exceptiontable, inconveniently as positional argument 14 (after linetable)
        code_args.insert(14, co.co_exceptiontable)

    code = code_type(*code_args)

    fn_args = [
        code,
        fn.__globals__,
        fn_name,
        fn.__defaults__,
        fn.__closure__,
        ]

    if _python_3_13_plus:
        fn_args.append(fn.__kwdefaults__)

    return fn_type(*fn_args)


# Test code
def sample_function(n=0):
    x = 1
    y = 2
    if n:
        return n * 2
    return x + y


def do_nothing():
    pass

do_nothing()  # Called for coverage


global_value = 0


def add_100_to_global_value():
    global global_value
    global_value += 100



class TestModifyBytecode(unittest.TestCase):

    def test_location_has_start_and_stop(self):
        """Test that Location objects have start and stop attributes."""
        loc = Location.position(sample_function, 1)
        self.assertIsInstance(loc.start, int)
        self.assertIsInstance(loc.stop, int)
        self.assertGreaterEqual(loc.stop, loc.start)

    def test_location_comparison_tuple_like(self):
        """Test Location comparison works like tuple comparison."""
        loc1 = Location(sample_function, 1, 2)
        loc2 = Location(sample_function, 1, 3)
        loc3 = Location(sample_function, 2, 3)

        # Same start, different stop
        self.assertLess(loc1, loc2)
        self.assertGreater(loc2, loc1)

        # Different start
        self.assertLess(loc1, loc3)
        self.assertLess(loc2, loc3)

    def test_location_comparison_different_functions(self):
        """Test that comparing Locations from different functions raises ValueError."""
        loc1 = Location.position(sample_function, 1)
        loc2 = Location.position(do_nothing, 1)

        with self.assertRaises(ValueError) as cm:
            loc1 < loc2
        self.assertIn("different functions", str(cm.exception))

    def test_location_comparison_operators(self):
        """Test that <=, >, >= work correctly for comparing Locations."""
        loc1 = Location(sample_function, 1, 2)
        loc2 = Location(sample_function, 1, 3)
        loc3 = Location(sample_function, 2, 3)

        # Test <=
        self.assertTrue(loc1 <= loc2)
        self.assertTrue(loc1 <= loc1)
        self.assertFalse(loc2 <= loc1)

        # Test >
        self.assertTrue(loc2 > loc1)
        self.assertTrue(loc3 > loc1)
        self.assertFalse(loc1 > loc2)

        # Test >=
        self.assertTrue(loc2 >= loc1)
        self.assertTrue(loc1 >= loc1)
        self.assertTrue(loc3 >= loc1)
        self.assertFalse(loc1 >= loc2)

    def test_location_comparison_not_implemented(self):
        """Test that comparing Location to non-Location returns NotImplemented."""
        loc = Location(sample_function, 1, 2)

        self.assertEqual(loc.__lt__(5), NotImplemented)
        self.assertEqual(loc.__le__(5), NotImplemented)
        self.assertEqual(loc.__gt__(5), NotImplemented)
        self.assertEqual(loc.__ge__(5), NotImplemented)
        self.assertEqual(loc.__eq__(5), NotImplemented)

    def test_location_rich_compare_with_different_functions(self):
        """Test that <=, >, >= with different functions raises ValueError."""
        loc1 = Location.position(sample_function, 1)
        loc2 = Location.position(do_nothing, 1)

        with self.assertRaises(ValueError) as cm:
            loc1 <= loc2
        self.assertIn("different functions", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            loc1 > loc2
        self.assertIn("different functions", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            loc1 >= loc2
        self.assertIn("different functions", str(cm.exception))

    def test_location_equality(self):
        """Test Location equality."""
        loc1 = Location(sample_function, 5, 7)
        loc2 = Location(sample_function, 5, 7)
        loc3 = Location(sample_function, 5, 8)

        self.assertEqual(loc1, loc2)
        self.assertNotEqual(loc1, loc3)

    def test_location_hash(self):
        """Test Location can be hashed."""
        loc1 = Location(sample_function, 5, 7)
        loc2 = Location(sample_function, 5, 7)

        # Should be able to use in sets/dicts
        location_set = {loc1, loc2}
        self.assertEqual(len(location_set), 1)

    def test_location_max(self):
        """Test using max() with Location objects."""
        loc1 = Location.position(sample_function, 1)
        loc2 = Location.position(sample_function, 3)
        loc3 = Location.position(sample_function, 2)

        max_loc = max([loc1, loc2, loc3])
        self.assertGreater(max_loc, loc1)
        self.assertGreater(max_loc, loc3)

    def test_location_repr(self):
        """Test Location repr."""
        loc = Location(sample_function, 5, 7)
        repr_str = repr(loc)
        self.assertIn("Location", repr_str)
        self.assertIn("sample_function", repr_str)
        self.assertIn("5", repr_str)
        self.assertIn("7", repr_str)

    def test_location_position_basic(self):
        """Test Location.position with basic line number."""
        loc = Location.position(sample_function, 2)
        self.assertIsInstance(loc, Location)
        self.assertEqual(loc.function, sample_function)
        self.assertGreaterEqual(loc.stop, loc.start)

    @skip_if_no_column_info
    def test_location_position_with_column(self):
        """Test Location.position with line and column."""
        loc = Location.position(sample_function, 2, 5)
        self.assertIsInstance(loc, Location)
        self.assertGreaterEqual(loc.stop, loc.start)

    @skip_if_column_info_is_available
    def test_location_position_column_not_supported_on_old_python(self):
        """Test that Location.position raises on Python 3.10- when column != 1."""
        with self.assertRaises(ValueError) as cm:
            Location.position(sample_function, 2, 5)
        self.assertIn("Python 3.10", str(cm.exception))
        self.assertIn("column", str(cm.exception).lower())

    def test_location_position_out_of_range(self):
        """Test that position outside function range raises ValueError."""
        with self.assertRaises(ValueError):
            Location.position(sample_function, 100)

    @skip_if_no_column_info
    def test_location_position_past_all_code_by_column(self):
        """Test Location.position when column is past all code on last line."""
        def simple_function():
            x = 1
            return x

        simple_function()  # Called for coverage

        # Get the number of lines in the function
        source_lines = inspect.getsource(simple_function).splitlines()
        last_line = len(source_lines)

        # Request a position on the last line at column 999
        with self.assertRaises(ValueError) as cm:
            Location.position(simple_function, last_line, 999)
        self.assertIn("No bytecode", str(cm.exception))

    @skip_if_no_column_info
    def test_location_position_with_corrupt_code_object(self):
        """Test that Location.position raises on functions with corrupt code objects."""
        # Test with invalid firstlineno
        stripped_invalid = _strip_line_and_column_information(sample_function, firstlineno=-1)
        with self.assertRaises(ValueError) as cm:
            Location.position(stripped_invalid, 1)
        self.assertIn("corrupt", str(cm.exception))

        # Test with missing line information
        stripped_no_lines = _strip_line_and_column_information(sample_function, firstlineno=None)
        with self.assertRaises(ValueError) as cm:
            Location.position(stripped_no_lines, 1)
        self.assertIn("corrupt", str(cm.exception))

    def test_strip_line_and_column_information_with_name_parameter(self):
        """Test that _strip_line_and_column_information can change function name."""
        stripped = _strip_line_and_column_information(
            sample_function,
            firstlineno=None,
            name='renamed_function'
        )
        self.assertEqual(stripped.__name__, 'renamed_function')
        self.assertEqual(stripped.__code__.co_name, 'renamed_function')

    @skip_if_no_column_info
    def test_location_text_basic(self):
        """Test Location.text with simple text search."""
        loc = Location.text(sample_function, "x = 1")
        self.assertIsInstance(loc, Location)
        self.assertEqual(loc.function, sample_function)
        self.assertGreaterEqual(loc.stop, loc.start)

    def test_location_text_not_found(self):
        """Test that missing text raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            Location.text(sample_function, "nonexistent")
        self.assertIn("not found", str(cm.exception))

    @skip_if_no_column_info
    def test_location_text_in_comment_not_found(self):
        """Test that text in comment raises ValueError (no bytecode for comments)."""
        def function_with_comment():
            x = 1  # unique comment marker text
            return x

        with self.assertRaises(ValueError) as cm:
            Location.text(function_with_comment, "unique comment marker")
        self.assertIn("not found", str(cm.exception))

    @skip_if_no_column_info
    def test_location_text_in_docstring_not_found(self):
        """Test that text in docstring raises ValueError (no bytecode for docstrings)."""
        def function_with_docstring():
            """This docstring contains rubber baby buggy bumpers."""
            x = 1
            return x

        with self.assertRaises(ValueError) as cm:
            Location.text(function_with_docstring, "rubber baby buggy bumpers")
        self.assertIn("not found", str(cm.exception))

    @skip_if_no_column_info
    def test_location_text_with_skip(self):
        """Test Location.text with skip parameter."""
        def function_with_duplicates():
            global global_value
            x = 1 - global_value
            y = 1 - global_value
            return x + y

        # Verify unmodified behavior
        global global_value
        global_value = 0
        self.assertEqual(function_with_duplicates(), 2)

        # Inject before first "= 1"
        global_value = 0
        loc0 = Location.text(function_with_duplicates, "= 1", skip=0)
        modified0 = inject_call(add_100_to_global_value, loc0)
        self.assertEqual(modified0(), -198)
        self.assertEqual(global_value, 100)

        # Inject before second "= 1"
        global_value = 0
        loc1 = Location.text(function_with_duplicates, "= 1", skip=1)
        modified1 = inject_call(add_100_to_global_value, loc1)
        self.assertEqual(modified1(), -98)
        self.assertEqual(global_value, 100)

    @skip_if_no_column_info
    def test_location_text_skip_out_of_range(self):
        """Test that skip beyond matches raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            Location.text(sample_function, "x = 1", skip=5)
        self.assertIn("cannot skip", str(cm.exception))

    @skip_if_no_column_info
    def test_location_text_with_after(self):
        """Test Location.text with after parameter."""
        global global_value
        global_value = 0

        def function_with_duplicates():
            global global_value
            x = 1 - global_value
            z = 1
            y = 2 - global_value
            z -= global_value
            return (x, y, z)

        self.assertEqual(function_with_duplicates(), (1, 2, 1))

        # Find location of "y", then find "z" after that
        y = Location.text(function_with_duplicates, "y")
        loc = Location.text(function_with_duplicates, "z", after=y)

        # Inject before the "z -=" line
        modified = inject_call(add_100_to_global_value, loc)
        result = modified()
        self.assertEqual(result, (1, 2, -99))

    @skip_if_no_column_info
    def test_location_text_with_after_using_max(self):
        """Test Location.text with after using max() of multiple constraints."""
        global global_value
        global_value = 0

        def function_with_duplicates():
            global global_value
            x = 1 - global_value
            z = 1
            y = 2 - global_value
            z -= global_value
            return (x, y, z)

        # Find "z" after the maximum of text "y" and text "2"
        y_and_2 = max([
            Location.text(function_with_duplicates, "y"),
            Location.text(function_with_duplicates, "2")
        ])
        loc = Location.text(function_with_duplicates, "z", after=y_and_2)

        modified = inject_call(add_100_to_global_value, loc)
        result = modified()
        self.assertEqual(result, (1, 2, -99))

    def test_location_token_basic(self):
        """Test Location.token with basic token search."""
        loc = Location.token(sample_function, "x")
        self.assertIsInstance(loc, Location)
        self.assertGreaterEqual(loc.stop, loc.start)

    def test_location_token_not_found(self):
        """Test that missing token raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            Location.token(sample_function, "nonexistent_token")
        self.assertIn("not found", str(cm.exception))

    def test_location_token_with_skip(self):
        """Test Location.token with skip parameter."""
        loc0 = Location.token(sample_function, "return", skip=0)
        loc1 = Location.token(sample_function, "return", skip=1)
        self.assertLess(loc0, loc1)

    @skip_if_no_column_info
    def test_location_token_skip_out_of_range(self):
        """Test that skip beyond matches raises ValueError for token."""
        with self.assertRaises(ValueError) as cm:
            Location.token(sample_function, "return", skip=10)
        self.assertIn("cannot skip", str(cm.exception))

    @skip_if_no_column_info
    def test_location_token_with_after_regression(self):
        """Regression test: token after text should respect text position within line."""
        global global_value
        global_value = 0

        def crazy_function(a):
            global global_value
            if a > 3:
                return (a * 2) - global_value
            foo = 1
            return (a * 3) - global_value

        # Verify unmodified behavior
        self.assertEqual(crazy_function(5), 10)
        self.assertEqual(crazy_function(2), 6)

        # Search for 'return' token after text "foo"
        foo_location = Location.text(crazy_function, "foo")
        loc = Location.token(crazy_function, 'return', after=foo_location)

        # Inject before the second return (the one in the else path)
        modified = inject_call(add_100_to_global_value, loc)

        # First branch shouldn't trigger injection
        global_value = 0
        self.assertEqual(modified(5), 10)
        self.assertEqual(global_value, 0)

        # Second branch should trigger injection
        global_value = 0
        self.assertEqual(modified(2), -94)
        self.assertEqual(global_value, 100)

    @skip_if_no_column_info
    def test_location_token_multiline(self):
        """Test Location.token with a multi-line token."""
        global global_value
        global_value = 0

        def function_with_multiline_strings():
            global global_value

            jabberwocky = '''
'Twas brillig, and the slithy toves
Did gyre and gimble in the wabe:
All mimsy were the borogoves,
And the mome raths outgrabe.
'''.ljust(3)
            jabberwocky_number = len(jabberwocky) - global_value

            the_crocodile = '''
How doth the little crocodile
     Improve his shining tail,
And pour the waters of the Nile
     On every golden scale!
'''.rjust(
    3)
            the_crocodile_number = len(the_crocodile) - global_value

            return (jabberwocky, jabberwocky_number, the_crocodile, the_crocodile_number)

        # Call unmodified function to get the strings
        jabberwocky, jabberwocky_number, the_crocodile, the_crocodile_number = function_with_multiline_strings()

        # Verify unmodified behavior
        self.assertEqual((jabberwocky_number, the_crocodile_number), (129, 122))

        # Find the first multi-line string token and inject before it
        loc = Location.token(function_with_multiline_strings, f"'''{jabberwocky}'''")
        modified = inject_call(add_100_to_global_value, loc)

        global_value = 0
        result = modified()
        self.assertEqual((result[1], result[3]), (29, 22))
        self.assertEqual(global_value, 100)

        # Find "the" after the first multiline string
        the_loc = Location.text(function_with_multiline_strings, 'the', after=loc)
        modified2 = inject_call(add_100_to_global_value, the_loc)

        global_value = 0
        result2 = modified2()
        self.assertEqual((result2[1], result2[3]), (129, 22))
        self.assertEqual(global_value, 100)

        # Search for "ljust" using Location.text
        ljust_text_loc = Location.text(function_with_multiline_strings, 'ljust')
        modified3 = inject_call(add_100_to_global_value, ljust_text_loc)

        global_value = 0
        result3 = modified3()
        self.assertEqual((result3[1], result3[3]), (29, 22))
        self.assertEqual(global_value, 100)

        # Search for "ljust" using Location.token
        ljust_token_loc = Location.token(function_with_multiline_strings, 'ljust')
        modified4 = inject_call(add_100_to_global_value, ljust_token_loc)

        global_value = 0
        result4 = modified4()
        self.assertEqual((result4[1], result4[3]), (29, 22))
        self.assertEqual(global_value, 100)

        # Search for "rjust" using Location.text to test multi-line range
        rjust_text_loc = Location.text(function_with_multiline_strings, 'rjust')
        modified5 = inject_call(add_100_to_global_value, rjust_text_loc)

        global_value = 0
        result5 = modified5()
        self.assertEqual((result5[1], result5[3]), (129, 22))
        self.assertEqual(global_value, 100)

        # Search for "rjust" using Location.token
        rjust_token_loc = Location.token(function_with_multiline_strings, 'rjust')
        modified6 = inject_call(add_100_to_global_value, rjust_token_loc)

        global_value = 0
        result6 = modified6()
        self.assertEqual((result6[1], result6[3]), (129, 22))
        self.assertEqual(global_value, 100)

    def test_location_bytecode_basic(self):
        """Test Location.bytecode with basic bytecode search."""
        loc = Location.bytecode(sample_function, "RETURN_VALUE")
        self.assertIsInstance(loc, Location)
        self.assertEqual(loc.stop, loc.start + 1)

    def test_location_bytecode_not_found(self):
        """Test that missing bytecode raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            Location.bytecode(sample_function, "NONEXISTENT_INSTRUCTION")
        self.assertIn("not found", str(cm.exception))

    def test_location_bytecode_with_skip(self):
        """Test Location.bytecode with skip parameter."""
        loc1 = Location.bytecode(sample_function, "RETURN_VALUE", skip=0)
        loc2 = Location.bytecode(sample_function, "RETURN_VALUE", skip=1)
        self.assertLess(loc1, loc2)

    def test_location_bytecode_skip_out_of_range(self):
        """Test that skip beyond matches raises ValueError for bytecode."""
        with self.assertRaises(ValueError) as cm:
            Location.bytecode(sample_function, "RETURN_VALUE", skip=10)
        self.assertIn("cannot skip", str(cm.exception))

    def test_location_bytecode_with_after(self):
        """Test Location.bytecode with after parameter."""
        # Find first RETURN_VALUE
        first_return = Location.bytecode(sample_function, "RETURN_VALUE", skip=0)
        # Find next RETURN_VALUE after it
        second_return = Location.bytecode(sample_function, "RETURN_VALUE", after=first_return)

        self.assertGreater(second_return, first_return)

    def test_inject_call_basic(self):
        """Test basic call injection."""
        call_count = [0]

        def injected():
            call_count[0] += 1

        loc = Location.position(sample_function, 1)
        modified = inject_call(injected, loc, name="test_func")
        result = modified()

        self.assertEqual(result, 3)
        self.assertEqual(call_count[0], 1)

    @skip_if_no_column_info
    def test_inject_call_at_text_location(self):
        """Test injection at a text-based location."""
        call_count = [0]

        def injected():
            call_count[0] += 1

        loc = Location.text(sample_function, "y = 2")
        modified = inject_call(injected, loc)
        result = modified()

        self.assertEqual(result, 3)
        self.assertEqual(call_count[0], 1)

    def test_inject_call_auto_name(self):
        """Test auto-naming when function name not in globals."""
        call_count = [0]

        def unique_function_name_12345():
            call_count[0] += 1

        self.assertNotIn('unique_function_name_12345', sample_function.__globals__)

        loc = Location.position(sample_function, 1)
        modified = inject_call(unique_function_name_12345, loc)
        result = modified()

        self.assertEqual(result, 3)
        self.assertEqual(call_count[0], 1)

    def test_inject_call_name_collision(self):
        """Test auto-naming with name collisions."""
        call_count = [0]

        def colliding_function():
            call_count[0] += 1

        sample_function.__globals__['colliding_function'] = lambda: None
        sample_function.__globals__['colliding_function_1'] = lambda: None

        try:
            loc = Location.position(sample_function, 1)
            modified = inject_call(colliding_function, loc)
            result = modified()

            self.assertEqual(result, 3)
            self.assertEqual(call_count[0], 1)

            self.assertIn('colliding_function', modified.__globals__)
            self.assertIn('colliding_function_1', modified.__globals__)
            self.assertIn('colliding_function_2', modified.__globals__)
        finally:
            del sample_function.__globals__['colliding_function']
            del sample_function.__globals__['colliding_function_1']

    def test_inject_call_explicit_name_collision(self):
        """Test that explicit name parameter raises ValueError when it already exists."""
        def some_function():
            pass

        some_function()  # Called for coverage

        # Put a name in the globals
        sample_function.__globals__['blammo'] = lambda: None

        try:
            loc = Location.position(sample_function, 1)
            with self.assertRaises(ValueError) as cm:
                inject_call(some_function, loc, name='blammo')
            self.assertIn("already exists", str(cm.exception))
            self.assertIn("blammo", str(cm.exception))
        finally:
            del sample_function.__globals__['blammo']

    def test_inject_call_string_name(self):
        """Test injection using string name from globals."""
        call_count = [0]

        def tracked_function():
            call_count[0] += 1

        sample_function.__globals__['tracked_function'] = tracked_function

        try:
            loc = Location.position(sample_function, 1)
            modified = inject_call('tracked_function', loc)
            result = modified()

            self.assertEqual(result, 3)
            self.assertEqual(call_count[0], 1)
        finally:
            del sample_function.__globals__['tracked_function']

    def test_inject_call_string_name_not_found(self):
        """Test that string name not in globals raises ValueError."""
        loc = Location.position(sample_function, 1)
        with self.assertRaises(ValueError) as cm:
            inject_call('nonexistent_function', loc)
        self.assertIn("not found in function globals", str(cm.exception))

    def test_sample_function_with_argument(self):
        """Test sample_function with argument to cover conditional branch."""
        result = sample_function(5)
        self.assertEqual(result, 10)

    def test_find_statement_end_with_endmarker(self):
        """Test _find_statement_end when statement ends with ENDMARKER."""
        tokens = [
            tokenize.TokenInfo(tokenize.NAME, 'return', (1, 0), (1, 6), 'return x'),
            tokenize.TokenInfo(tokenize.NAME, 'x', (1, 7), (1, 8), 'return x'),
            tokenize.TokenInfo(tokenize.ENDMARKER, '', (2, 0), (2, 0), ''),
        ]

        result = _find_statement_end(tokens)
        self.assertEqual(result, len(tokens) - 1)

    def test_location_token_endmarker(self):
        """Test that searching for ENDMARKER token raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            Location.token(sample_function, 'ENDMARKER')
        self.assertIn('ENDMARKER', str(cm.exception))
        self.assertIn('bytecode', str(cm.exception))

    def test_inject_call_on_closure(self):
        """A closure (function with free variables) starts with a
        COPY_FREE_VARS / MAKE_CELL prologue instruction whose
        position info is None.  inject_call must skip such prologue
        instructions when locating the injection point and must
        still produce a working modified function."""
        captured = 10

        def closure_fn():
            return captured + 5

        # Sanity check: this IS a closure on Pythons where
        # closures are implemented with cell-based capture.
        self.assertEqual(closure_fn(), 15)
        self.assertGreater(len(closure_fn.__code__.co_freevars), 0)

        call_count = [0]
        def injected():
            call_count[0] += 1

        loc = Location.text(closure_fn, "return captured")
        modified = inject_call(injected, loc)
        result = modified()
        self.assertEqual(result, 15)
        self.assertEqual(call_count[0], 1)

    def test_location_position_on_closure(self):
        """Location.position works on a closure: the prologue
        instruction with no source position is skipped, and the
        first instruction at the requested line is returned."""
        captured = 7

        def closure_fn():
            x = captured
            return x

        loc = Location.position(closure_fn, 2)  # the `x = captured` line
        self.assertIsInstance(loc, Location)
        self.assertGreaterEqual(loc.stop, loc.start)

        call_count = [0]
        def injected():
            call_count[0] += 1

        modified = inject_call(injected, loc)
        self.assertEqual(modified(), 7)
        self.assertEqual(call_count[0], 1)

    @skip_if_no_column_info
    def test_location_text_on_closure(self):
        """Location.text works on a closure even though its first
        bytecode instruction (COPY_FREE_VARS) has no position info."""
        captured = 100

        def closure_fn():
            y = captured
            return y - 50

        # Two distinct matches; verify both work despite the prologue.
        loc1 = Location.text(closure_fn, "captured")
        loc2 = Location.text(closure_fn, "- 50")
        self.assertLess(loc1, loc2)

    def test_corrupt_code_object_check_still_works_on_closure(self):
        """The relaxed validation rejects only functions whose
        instructions ALL lack position info -- not functions that
        merely have a positionless prologue (closures)."""
        # A closure: positionless prologue but real-source instructions
        # afterward.  Must NOT raise.
        captured = 1
        def closure_fn():
            return captured
        Location.position(closure_fn, 1)  # should not raise

        # A function whose entire code object has been stripped of
        # position info: still raises.
        stripped = _strip_line_and_column_information(sample_function, firstlineno=None)
        with self.assertRaises(ValueError) as cm:
            Location.position(stripped, 1)
        self.assertIn("corrupt", str(cm.exception))

def run_tests():
    blankettestlib.run(name="blanket.injector", module=__name__)

if __name__ == '__main__':
    run_tests()
    blankettestlib.finish()
