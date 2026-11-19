"""Fictional review scenarios: static evidence is never semantic/test acceptance."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'Makefile').is_file())
SPEC = importlib.util.spec_from_file_location('scope_verifier', ROOT/'skills/_shared/scripts/verify.py')
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)

class ScopeReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('skills/example/scripts', 'scripts', 'tests/integration', 'docs'):
            (self.root/name).mkdir(parents=True, exist_ok=True)
        (self.root/'AGENTS.md').write_text('Read docs/architecture.md and SCOPE.md.\n')
        (self.root/'docs/architecture.md').write_text('Runtime belongs under skills/.\n')
        self.source = self.root/'skills/example/scripts/runtime.py'
        self.source.write_text("raise RuntimeError('must never execute inspected code')\n")
        (self.root/'tests/integration/test_example.py').write_text("raise RuntimeError('must never run target tests')\n")
        self.scope = 'Status: confirmed\n\n## R1: Consent\nStatus: confirmed\nAcceptance: Do not write files without consent.\nSource: skills/example/scripts/runtime.py\nTest: tests/integration/test_example.py\n'
        (self.root/'SCOPE.md').write_text(self.scope)

    def snapshot(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file() and not p.is_symlink()}

    def test_generator_literal_is_not_an_unimplemented_source(self):
        self.source.write_text('MARKER = "<!-- plugin-skeleton: unimplemented -->"\n')
        self.assertNotIn('skeleton_unimplemented', {f['code'] for f in verify.scope_review(self.root)['findings']})

    def test_available_evidence_never_claims_semantic_compliance_or_test_success(self):
        before = self.snapshot()
        report = verify.scope_review(self.root)
        self.assertEqual('ready_for_source_review', report['status'])
        self.assertEqual('unverified', report['requirements'][0]['semantic_status'])
        self.assertEqual('not_run', report['test_execution'])
        self.assertFalse(report['target_code_executed'])
        self.assertEqual(before, self.snapshot())
        self.assertTrue(all(len(item['sha256']) == 64 for item in report['evidence']))

    def test_draft_missing_acceptance_and_evidence_are_explained(self):
        (self.root/'SCOPE.md').write_text('Status: draft\n\n## R1: Pending\nStatus: draft\n')
        report = verify.scope_review(self.root)
        codes = {item['code'] for item in report['findings']}
        self.assertTrue({'scope_unconfirmed','requirement_unconfirmed','acceptance_missing','missing_sources','missing_tests'} <= codes)
        for item in report['findings']:
            self.assertTrue(item['reason']); self.assertTrue(item['recommendation']);self.assertGreater(item['line'],0)

    def test_missing_scope_never_infers_requirements_from_source(self):
        (self.root/'SCOPE.md').unlink()
        report = verify.scope_review(self.root)
        self.assertEqual([], report['requirements'])
        self.assertEqual('needs_attention',report['status'])

    def test_private_and_symlink_evidence_not_read(self):
        (self.root/'.env').write_text('SECRET=never-return-this\n')
        (self.root/'skills/example/scripts/link.py').symlink_to(self.root/'.env')
        for pointer in ('.env','../outside.py','skills/example/scripts/link.py','tests/fixtures/candidate.md'):
            with self.subTest(pointer=pointer):
                (self.root/'SCOPE.md').write_text(self.scope.replace('skills/example/scripts/runtime.py',pointer))
                report=verify.scope_review(self.root)
                self.assertIn('evidence_unavailable', {f['code'] for f in report['findings']})
                self.assertNotIn('never-return-this', str(report))

    def test_skeleton_and_runtime_importing_development_tools_are_reported(self):
        self.source.write_text('# <!-- plugin-skeleton: unimplemented -->\nfrom scripts.development import helper\n')
        (self.root/'scripts/development.py').write_text("raise RuntimeError('never import me')\n")
        (self.root/'tests/regression').mkdir()
        report=verify.scope_review(self.root)
        self.assertTrue({'skeleton_unimplemented','runtime_imports_development_tool','legacy_test_layout'} <= {f['code'] for f in report['findings']})
        self.source.write_text('from .scripts.development import helper\n')
        self.assertNotIn('runtime_imports_development_tool', {f['code'] for f in verify.scope_review(self.root)['findings']})

    def test_duplicate_requirements_and_changed_source_evidence(self):
        before=verify.scope_review(self.root)['evidence']
        self.source.write_text('def action():\n    return None\n')
        after=verify.scope_review(self.root)['evidence']
        self.assertNotEqual(before, after)
        (self.root/'SCOPE.md').write_text(self.scope+'\n'+self.scope[self.scope.index('## R1:'):])
        self.assertIn('duplicate_requirement', {f['code'] for f in verify.scope_review(self.root)['findings']})

    def test_confirmed_behavior_contradiction_is_not_falsely_certified_by_pointers(self):
        self.source.write_text("from pathlib import Path\ndef action(consent):\n    Path('state.md').write_text('writes even without consent')\n")
        report = verify.scope_review(self.root)
        self.assertEqual('unverified', report['semantic_status'])
        self.assertEqual('not_run',report['requirements'][0]['test_execution'])
        instructions = (ROOT/'skills/_shared/references/scope-review.md').read_text()
        for rule in ('contradicted', 'missing_evidence', 'file and line evidence', 'Never repair', 'Keep the confirmed target unchanged'):
            self.assertIn(rule, instructions)
