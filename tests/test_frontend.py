import copy
import unittest

from foundation.errors import FoundationError
from foundation.ir import canonical, identity, integer, load, loads, validate_program
from foundation.source import parse_source


class FrontendTests(unittest.TestCase):
    def test_real_resilient_signature_and_source_spans(self):
        source = 'fn nonnegative(int x) -> int { if x >= 0 { return x; } else { return 0; } }'
        candidate, source_map = parse_source(source)
        oracle = load('examples/nonnegative/candidate-ir.json')
        self.assertEqual(candidate['function'], oracle['function'])
        for span in source_map['spans']:
            self.assertEqual(source[span['start']:span['end']], span['excerpt'])

    def test_precedence_is_machine_arithmetic(self):
        candidate, _ = parse_source('fn f(int x) -> int { return x + 2 * 3; }')
        self.assertEqual(candidate['function']['body']['op'], 'add_wrap')
        self.assertEqual(candidate['function']['body']['right']['op'], 'mul_wrap')

    def test_minimum_literal_is_not_a_host_float_or_unary_overflow(self):
        candidate, _ = parse_source('fn f() -> int { return -9223372036854775808; }')
        self.assertEqual(candidate['function']['body']['value'], '-9223372036854775808')

    def test_unsupported_code_is_never_discarded(self):
        for source in [
            'fn f(int x) -> int { return x; } fn hidden() -> int { return 1; }',
            'fn f(int x) -> int { return external(x); }',
            'fn f(int x) -> int { let y = x; return y; }',
            'fn f(int x) -> int requires false { return x; }',
            'fn f(int x) -> int { if x > 0 { return x; } }',
        ]:
            with self.subTest(source=source), self.assertRaises(FoundationError):
                parse_source(source)

    def test_duplicate_and_imprecise_json_are_rejected(self):
        for text in ['{"x":"1","x":"2"}', '{"x":1.5}', '{"x":NaN}']:
            with self.subTest(text=text), self.assertRaises(FoundationError):
                loads(text)
        for value in [1, '9223372036854775808', '-0', '01', '+1']:
            with self.subTest(value=value), self.assertRaises(FoundationError):
                integer(value)

    def test_wire_typing_rejects_even_dead_branches(self):
        p = load('examples/nonnegative/spec-ir.json')
        broken = copy.deepcopy(p)
        broken['function']['body']['else'] = {'kind': 'var', 'type': 'i64', 'name': 'missing'}
        with self.assertRaises(FoundationError):
            validate_program(broken)
        broken = copy.deepcopy(p)
        broken['function']['body']['condition']['op'] = 'unsigned_ge'
        with self.assertRaises(FoundationError) as error:
            validate_program(broken)
        self.assertEqual(error.exception.outcome, 'Unsupported')

    def test_canonical_identity_is_domain_separated_and_order_invariant(self):
        self.assertEqual(canonical({'b': '2', 'a': '1'}), canonical({'a': '1', 'b': '2'}))
        self.assertNotEqual(identity('source-ir', {'a': '1'}), identity('target-ir', {'a': '1'}))

    def test_flat_operator_chain_has_a_typed_resource_limit(self):
        source = 'fn f(int x) -> int { return ' + ' + '.join(['x'] * 700) + '; }'
        with self.assertRaises(FoundationError) as error:
            parse_source(source)
        self.assertEqual(error.exception.outcome, 'ResourceLimit')


if __name__ == '__main__':
    unittest.main()
