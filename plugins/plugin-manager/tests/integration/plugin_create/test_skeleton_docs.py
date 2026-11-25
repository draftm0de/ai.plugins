"""R4: finished skeleton pages are real Markdown files (templates/skeleton-docs), not a JSON with placeholders."""
import json
from pathlib import Path
import re
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
SHARED = ROOT / 'skills/_shared'


class SkeletonDocsTests(unittest.TestCase):
    def test_every_outline_page_exists_finished_with_only_the_title_placeholder(self):
        outline = json.loads((SHARED / 'templates/outline.json').read_text(encoding='utf-8'))['plugin']
        for template, headings in outline.items():
            with self.subTest(page=template):
                text = (SHARED / 'templates/skeleton-docs' / template).read_text(encoding='utf-8')
                expected = ['{{TITLE}}'] if template.startswith('README') else ['{{SKILL_ROWS}}', '{{SKILL_SECTIONS}}'] if template.endswith('/skills.md') else []
                self.assertEqual(expected, re.findall(r'\{\{[A-Z_0-9]+\}\}', text))
                self.assertEqual(headings, re.findall(r'^## (.+)$', text, re.M))

    def test_json_content_file_is_gone_and_no_page_is_unlisted(self):
        self.assertFalse((SHARED / 'templates/skeleton-content.json').exists())
        outline = json.loads((SHARED / 'templates/outline.json').read_text(encoding='utf-8'))['plugin']
        found = {str(p.relative_to(SHARED / 'templates/skeleton-docs')) for p in (SHARED / 'templates/skeleton-docs').rglob('*.md')}
        self.assertEqual(set(outline), found)

    def test_each_kind_has_a_template_for_every_page_of_its_outline(self):  # R34
        outline = json.loads((SHARED / 'templates/outline.json').read_text(encoding='utf-8'))
        self.assertEqual({'plugin', 'marketplace'}, set(outline))
        self.assertNotIn('docs/en/skills.md', outline['marketplace'])
        self.assertIn('docs/en/plugins.md', outline['marketplace'])
        for kind, pages in outline.items():
            found = {str(p.relative_to(SHARED / 'templates/documentation' / kind)) for p in (SHARED / 'templates/documentation' / kind).rglob('*.md')}
            self.assertEqual(set(pages), found, kind)


if __name__ == '__main__':
    unittest.main()
