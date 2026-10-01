"""Conformance cases for reporting implementation progress without proof claims."""
import unittest
from pathlib import Path
import hashlib
import json
import tempfile
from unittest.mock import patch

from validate_spec import check_work_package_status, check_backend_status


class WorkPackageStatusTests(unittest.TestCase):
    def test_planned_requires_no_implementation(self):
        check_work_package_status({'status': 'planned'})

    def test_progress_binds_to_existing_implementation(self):
        check_work_package_status({
            'status': 'in_progress',
            'implementation_artifacts': ['crates/foundation-core/src/lib.rs'],
        })

    def test_progress_cannot_be_asserted_without_artifacts(self):
        for artifacts in [[], ['missing.rs'], ['../Resilient/README.md'], ['/etc/hosts']]:
            with self.subTest(artifacts=artifacts), self.assertRaises(ValueError):
                check_work_package_status({'status': 'in_progress', 'implementation_artifacts': artifacts})

    def test_completion_is_not_inferred_from_files_or_labels(self):
        for status in ['implemented', 'complete', 'Proved', 'Accepted']:
            with self.subTest(status=status), self.assertRaises(ValueError):
                check_work_package_status({
                    'status': status,
                    'implementation_artifacts': ['crates/foundation-core/src/lib.rs'],
                })


class BackendStatusTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        (self.root / 'checker.py').write_text('checker')
        digest = hashlib.sha256(b'checker').hexdigest()
        self.report = {'status': 'passed', 'scope': 'scalar_e2e_conformance',
                       'policy': 'scalar_source_exact_trusted_rust_v1',
                       'capability_ids': ['scalar-smt'], 'tests_run': 34,
                       'tests_failed': 0, 'tests_skipped': 0, 'oracle_cases_executed': 5,
                       'formal_class': 'solver_checked', 'translation_class': 'translation_checked',
                       'native_relation': 'trusted_compilation',
                       'implementation_hashes': {'checker.py': digest}, 'test_hashes': {'checker.py': digest},
                       'driver_hashes': {'checker.py': digest}, 'evidence_files': {'checker.py': digest}}
        self.route = {'id': 'scalar-smt', 'status': 'experimental', 'checker_status': 'implemented',
                      'implementation_artifacts': ['checker.py'], 'evidence_report': 'report.json',
                      'evidence_classes': ['solver_checked']}

    def check(self):
        (self.root / 'report.json').write_text(json.dumps(self.report))
        with patch('validate_spec.ROOT', self.root):
            check_backend_status(self.route)

    def test_experimental_requires_bound_recorded_run(self):
        self.check()
        (self.root / 'checker.py').write_text('changed')
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_or_failed_gate_cannot_promote_capability(self):
        for field, value in [('tests_skipped', 1), ('tests_failed', 1), ('tests_run', 0),
                             ('capability_ids', []), ('evidence_files', {}), ('status', 'NotRun')]:
            with self.subTest(field=field):
                saved = self.report[field]
                self.report[field] = value
                with self.assertRaises(ValueError):
                    self.check()
                self.report[field] = saved

    def test_empirical_report_cannot_create_kernel_or_released_claim(self):
        for field, value in [('status', 'released'), ('checker_status', 'mechanized'),
                             ('evidence_classes', ['kernel_checked'])]:
            with self.subTest(field=field):
                saved = self.route[field]
                self.route[field] = value
                with self.assertRaises(ValueError):
                    self.check()
                self.route[field] = saved

    def test_planned_route_cannot_claim_implemented_checker(self):
        with self.assertRaises(ValueError):
            check_backend_status({'status': 'planned', 'checker_status': 'implemented'})


if __name__ == '__main__':
    unittest.main()
