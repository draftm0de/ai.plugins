"""R4: finished skeleton pages are real Markdown files (templates/skeleton-docs), not a JSON with placeholders."""
import json
from pathlib import Path
import re
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
SHARED = ROOT / 'skills/_shared'


class SkeletonDocsTests(unittest.TestCase):
    def test_every_outline_page_exists_finished_with_only_the_title_placeholder(self):
        outline = json.loads((SHARED / 'templates/outline.json').read_text(encoding='utf-8'))
        for template, headings in outline.items():
            with self.subTest(page=template):
                text = (SHARED / 'templates/skeleton-docs' / template).read_text(encoding='utf-8')
                self.assertEqual(['{{TITLE}}'] if template.startswith('README') else [], re.findall(r'\{\{[A-Z_0-9]+\}\}', text))
                self.assertEqual(headings, re.findall(r'^## (.+)$', text, re.M))

    def test_json_content_file_is_gone_and_no_page_is_unlisted(self):
        self.assertFalse((SHARED / 'templates/skeleton-content.json').exists())
        outline = json.loads((SHARED / 'templates/outline.json').read_text(encoding='utf-8'))
        found = {str(p.relative_to(SHARED / 'templates/skeleton-docs')) for p in (SHARED / 'templates/skeleton-docs').rglob('*.md')}
        self.assertEqual(set(outline), found)


if __name__ == '__main__':
    unittest.main()
