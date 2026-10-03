"""Versioned controlled-language templates; unrestricted prose needs a decision."""
from .errors import FoundationError
from .ir import PROFILE, VERSION, binary, node, program

SENTENCE = 'For an integer x, return x if x is nonnegative, and return zero otherwise.'
TEMPLATE_ID = 'nonnegative-i64-v1'
CLAMP_SENTENCE = 'For an integer x, clamp x to the inclusive range [-10, 10].'
CLAMP_TEMPLATE_ID = 'clamp-i64-minus10-plus10-v1'


def intent_identity(ledger):
    template = TEMPLATE_ID if ledger['task_id'] == 'nonnegative' else CLAMP_TEMPLATE_ID
    return {'mode': 'controlled_language', 'status': 'accepted', 'template': template}


def interpret_clamp(text):
    x = node('var', 'i64', name='x')
    lower, upper = node('int', 'i64', value='-10'), node('int', 'i64', value='10')
    above = node('if', 'i64', condition=binary('gt_signed', x, upper), then=upper, **{'else': x})
    body = node('if', 'i64', condition=binary('lt_signed', x, lower), then=lower, **{'else': above})
    spec = program(body, [{'name': 'x', 'type': 'i64'}], 'clamp', 'spec-clamp')
    start = text.index(CLAMP_SENTENCE)
    groups = [('LOWER', ['CLAMP-MIN', 'CLAMP-BELOW', 'CLAMP-LOWER']),
              ('INTERIOR', ['CLAMP-LOWER-INNER', 'CLAMP-ZERO', 'CLAMP-UPPER-INNER']),
              ('UPPER', ['CLAMP-UPPER', 'CLAMP-ABOVE', 'CLAMP-MAX'])]
    ledger = {
        'version': VERSION, 'kind': 'requirement_ledger', 'illustrative': False,
        'task_id': 'clamp', 'intent_mode': 'controlled_language',
        'source_artifact_id': 'request', 'interpretation_state': 'accepted',
        'decision_provenance': 'Explicit template ' + CLAMP_TEMPLATE_ID + ' under ' + PROFILE + '; input domain is all i64; endpoints are inclusive -10 and 10.',
        'requirements': [{
            'id': 'R-CLAMP-' + name, 'text': CLAMP_SENTENCE, 'source_excerpt': CLAMP_SENTENCE,
            'source_span': {'start': start, 'end': start + len(CLAMP_SENTENCE)},
            'decision': 'accepted', 'clause_ids': ['C-CLAMP-' + name], 'oracle_case_ids': cases,
            'assumptions': ['Integer is signed wrapping i64; this fixed template has no arithmetic operations or excluded inputs.'],
        } for name, cases in groups], 'unresolved_ambiguities': [],
    }
    return spec, ledger


def interpret(text):
    sentence = text.strip()
    if sentence == CLAMP_SENTENCE:
        return interpret_clamp(text)
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
