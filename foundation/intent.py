"""One versioned controlled-language template; unrestricted prose needs a decision."""
from .errors import FoundationError
from .ir import PROFILE, VERSION, binary, node, program

SENTENCE = 'For an integer x, return x if x is nonnegative, and return zero otherwise.'
TEMPLATE_ID = 'nonnegative-i64-v1'


def interpret(text):
    sentence = text.strip()
    if sentence != SENTENCE:
        raise FoundationError('NeedsDecision', 'Request does not match a supported controlled-language template', 'intent')
    x, zero = node('var', 'i64', name='x'), node('int', 'i64', value='0')
    body = node('if', 'i64', condition=binary('ge_signed', x, zero), then=x, **{'else': zero})
    spec = program(body, [{'name': 'x', 'type': 'i64'}], 'nonnegative', 'spec-nonnegative')
    start = text.index(sentence)
    ledger = {
        'version': VERSION, 'kind': 'requirement_ledger', 'illustrative': False,
        'task_id': 'nonnegative', 'intent_mode': 'controlled_language',
        'source_artifact_id': 'request', 'interpretation_state': 'accepted',
        'decision_provenance': 'Explicit template ' + TEMPLATE_ID + ' under ' + PROFILE + '; input domain is all i64.',
        'requirements': [{
            'id': 'R-NN-EXACT', 'text': sentence, 'source_excerpt': sentence,
            'source_span': {'start': start, 'end': start + len(sentence)},
            'decision': 'accepted', 'clause_ids': ['C-NN-EXACT'],
            'oracle_case_ids': ['NN-MIN', 'NN-NEG', 'NN-ZERO', 'NN-POS', 'NN-MAX'],
            'assumptions': ['Integer is signed wrapping i64 by the versioned template domain.'],
        }],
        'unresolved_ambiguities': [],
    }
    return spec, ledger
