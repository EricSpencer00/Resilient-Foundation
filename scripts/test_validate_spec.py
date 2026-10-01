"""Conformance cases for reporting implementation progress without proof claims."""
import unittest

from validate_spec import check_work_package_status


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


if __name__ == '__main__':
    unittest.main()
