import unittest

from foundation.ir import load
from foundation.smt import decode_value, equivalence_query


class SMTEncodingTests(unittest.TestCase):
    def test_query_observes_errors_and_uses_signed_order(self):
        spec = load('examples/nonnegative/spec-ir.json')
        query, variables = equivalence_query(spec, spec)
        self.assertEqual(variables, ['p0'])
        self.assertIn('(bvsge ', query)
        self.assertIn('(xor ', query)
        self.assertIn('(not (= ', query)
        self.assertNotIn('forall', query)

    def test_decoding_preserves_min_max_and_json_precision(self):
        self.assertEqual(decode_value('#x8000000000000000', 'i64'), '-9223372036854775808')
        self.assertEqual(decode_value('#x7fffffffffffffff', 'i64'), '9223372036854775807')
        self.assertEqual(decode_value(['_', 'bv9007199254740993', '64'], 'i64'), '9007199254740993')


if __name__ == '__main__':
    unittest.main()
