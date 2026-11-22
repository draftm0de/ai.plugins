"""Unit tests of the shared operator-language helper (fictional data only)."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.support.operator_language_fixture import GENERATOR, HELPER, load


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.module = load(GENERATOR / HELPER)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, content):
        (self.root / '.project').mkdir(exist_ok=True)
        (self.root / '.project/operator.json').write_text(content, encoding='utf-8')

    def test_valid_language_tags(self):
        for value in ('de', 'en', 'fr', 'pt-BR', 'zh-Hant', 'haw', 'sr-Latn-RS', 'es-419'):
            with self.subTest(value=value):
                self.module.validate_language(value)

    def test_invalid_language_values(self):
        for value in ('', 'D', 'de_DE', 'DE', 'deu1', 'de-', 'de--x', ' de', 'de\n', 'de/../x', 'x' * 4, None, 5, True, ['de']):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.module.validate_language(value)

    def test_wrong_json_types_and_formats_are_rejected(self):
        cases = ('[]', '"de"', 'null', '1', '{}', '{"schema_version": 1}',
                 '{"schema_version": "1", "operator_language": "de"}',
                 '{"schema_version": true, "operator_language": "de"}',
                 '{"schema_version": 1.0, "operator_language": "de"}',
                 '{"schema_version": 2, "operator_language": "de"}',
                 '{"schema_version": 0, "operator_language": "de"}',
                 '{"schema_version": 1, "operator_language": 7}',
                 '{"schema_version": 1, "operator_language": null}',
                 '{"schema_version": 1, "operator_language": "de", "extra": 1}',
                 '{"schema_version": 1, "operator_language": "not valid"}')
        for content in cases:
            with self.subTest(content=content):
                self.write(content)
                for call in ((), ('de',)):
                    with self.assertRaises(ValueError):
                        self.module.preference(self.root, *call)
                self.assertEqual(content, (self.root / '.project/operator.json').read_text())

    def test_corrupt_json_and_encoding_are_value_errors(self):
        self.write('{')
        with self.assertRaises(ValueError): self.module.preference(self.root)
        (self.root / '.project/operator.json').write_bytes(b'\xff\xfe\x00')
        with self.assertRaises(ValueError): self.module.preference(self.root)

    def test_result_structure(self):
        self.assertEqual({'operator_language': None, 'needs_choice': True}, self.module.preference(self.root))
        self.assertEqual({'operator_language': 'pt-BR', 'needs_choice': False}, self.module.preference(self.root, 'pt-BR'))
        self.assertEqual({'operator_language': 'pt-BR', 'needs_choice': False}, self.module.preference(self.root))
        self.assertEqual('{\n  "schema_version": 1,\n  "operator_language": "pt-BR"\n}\n',
                         (self.root / '.project/operator.json').read_text())

    def test_missing_project_is_rejected(self):
        with self.assertRaises(ValueError): self.module.preference(self.root / 'absent')


if __name__ == '__main__':
    unittest.main()
