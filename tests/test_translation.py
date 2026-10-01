import copy
import unittest

from foundation.errors import FoundationError
from foundation.ir import load
from foundation.native import decode, emit


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.model = load('examples/nonnegative/spec-ir.json')
        self.model['illustrative'] = False

    def test_constructor_decode_retains_observed_function(self):
        target = decode(emit(self.model))
        self.assertEqual(target['function']['body'], self.model['function']['body'])
        self.assertEqual(target['function']['params'], self.model['function']['params'])

    def test_wrong_arithmetic_is_visible_to_target_reader(self):
        model = copy.deepcopy(self.model)
        model['function']['body'] = {'kind': 'binary', 'type': 'i64', 'op': 'add_wrap',
                                   'left': {'kind': 'var', 'type': 'i64', 'name': 'x'},
                                   'right': {'kind': 'int', 'type': 'i64', 'value': '1'}}
        target = decode(emit(model).replace('BinaryOp::AddWrap', 'BinaryOp::SubWrap'))
        self.assertEqual(target['function']['body']['op'], 'sub_wrap')

    def test_added_effects_or_runtime_code_are_rejected(self):
        source = emit(self.model)
        for changed in [source + '\nfn hidden() {}', source.replace('let model = model();', 'std::process::exit(0);')]:
            with self.assertRaises(FoundationError):
                decode(changed)


if __name__ == '__main__':
    unittest.main()
