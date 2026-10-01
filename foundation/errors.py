EXIT_CODES = {
    'Refuted': 2, 'Unknown': 3, 'Timeout': 3, 'ResourceLimit': 3,
    'Unsupported': 4, 'InvalidEvidence': 5, 'NeedsDecision': 6, 'Error': 1,
}


class FoundationError(Exception):
    def __init__(self, outcome, reason, stage='validation', **details):
        super().__init__(reason)
        self.outcome = outcome
        self.reason = reason
        self.stage = stage
        self.details = details

    def as_dict(self):
        return {'outcome': self.outcome, 'stage': self.stage, 'reason': self.reason, **self.details}
