"""Check migration boundaries and complete source-content coverage."""
import _bootstrap
from collections import defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from collaboration_import import SECTION_IDS, code_text, course_sections, source_sections, text_content
from content import CHAPTERS, SOURCES, slides, _deleted_slides

ARCHIVE = ROOT / 'archive' / '2026-10-07-before-collaboration-import'


def normalized(text):
    return re.sub(r'\s+', '', text)


class PayloadText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = defaultdict(list)
        self.active = None
        self.depth = 0
        self.pre_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'data-import-block' in attributes:
            self.active = attributes['data-import-block']
            self.depth = 0
        if self.active and tag not in ('br', 'hr', 'img', 'input'):
            self.depth += 1
        if tag == 'pre':
            self.pre_depth += 1

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.pre_depth -= 1
        if self.active:
            self.depth -= 1
            if not self.depth:
                self.active = None

    def handle_data(self, value):
        if self.active:
            self.fragments[self.active].append((bool(self.pre_depth), value))


class CollaborationMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ARCHIVE / 'slides.json').read_text(encoding='utf-8'))
        cls.imported = [slide for slide in slides if slide.get('source_section')]

    def test_new_order_preserves_front_and_removes_original_tail(self):
        # Copy can be edited; page order, timing, references and demo hooks stay.
        front = [slides[0], *slides[2:12]]
        for actual, original in zip(front, self.original[:11]):
            for key in ('title', 'chapter', 'seconds', 'layout', 'sources'):
                self.assertEqual(actual[key], original[key])
            hooks = r'data-outing-[\w-]+(?:="[^"]*")?'
            self.assertEqual(re.findall(hooks, actual['body']),
                             re.findall(hooks, original['body']))
        self.assertEqual(slides[12]['title'], '五种协作模式总览')
        self.assertEqual(len(slides), 39)
        self.assertEqual(slides[-1]['title'], '关键挑战与决策矩阵 · 性能目标示例')
        self.assertFalse({slide['title'] for slide in _deleted_slides}.intersection(slide['title'] for slide in slides))
        removed_titles = {slide['title'] for slide in self.original[11:]}
        self.assertFalse(removed_titles.intersection(slide['title'] for slide in slides))

    def test_source_sections_are_complete_and_in_order(self):
        actual = list(dict.fromkeys(slide['source_section'] for slide in self.imported))
        self.assertEqual(actual, ['sec02', 'training', *SECTION_IDS[6:-2]])
        self.assertIn('性能目标示例', self.imported[-1]['title'])

    def test_all_prose_tables_and_code_survive_pagination(self):
        parser = PayloadText()
        deleted = PayloadText()
        for slide in _deleted_slides:
            deleted.feed(slide['body'])
        for slide in self.imported:
            parser.feed(slide['body'])
        for section_id, section in course_sections().items():
            if section_id in ('sec03', 'sec04', 'sec05', 'sec06', 'sec07', 'sec08'):
                # Authorized teaching redesign: framework fragments remain in
                # the local source snapshot rather than on the main slides.
                self.assertIn(f'id="{section_id}"', (ROOT / 'assets/imported/multi-agent-source.html').read_text(encoding='utf-8'))
                continue
            for index, block in enumerate(section['blocks']):
                key = f'{section_id}:{index}'
                if key in deleted.fragments:
                    continue
                with self.subTest(block=key):
                    self.assertIn(key, parser.fragments)
                    original_code = code_text(block)
                    fragments = parser.fragments[key]
                    actual = ''.join(value for in_pre, value in fragments
                                     if original_code is None or in_pre)
                    expected = original_code if original_code is not None else text_content(block)
                    self.assertEqual(normalized(actual), normalized(expected))

    def test_overview_is_one_page_with_source_descriptions_and_reviewed_details(self):
        original, revised = source_sections(), course_sections()
        for section_id in SECTION_IDS:
            if section_id not in ('sec02', 'sec04', 'sec05', 'sec06', 'sec07', 'sec09', 'sec10', 'sec11'):
                self.assertEqual(original[section_id], revised[section_id])
        self.assertEqual(sum(slide.get('source_section') == 'sec02' for slide in slides), 1)
        comparison = slides[12]['body']
        # Source names remain traceable while descriptions can be edited.
        names = re.findall(r'<h4>(.*?)</h4>', original['sec02']['blocks'][1], re.S)
        for name in names:
            for part in text_content(name).split(' · '):
                self.assertIn(part, text_content(comparison))
        self.assertNotIn('<table', comparison)
        self.assertEqual(re.findall(r'data-comparison-pattern="(.*?)"', comparison),
                         ['supervisor', 'hierarchical', 'swarm', 'sequential', 'network'])
        self.assertEqual(comparison.count('role="img"'), 5)
        self.assertIn('不是固定循环', comparison)
        self.assertIn('Swarm', code_text(revised['sec05']['blocks'][6]))
        self.assertNotIn('RoundRobinGroupChat', code_text(revised['sec05']['blocks'][6]))
        network_code = code_text(revised['sec07']['blocks'][5])
        self.assertNotIn('router_node', network_code)
        self.assertIn('Command(update=', network_code)
        self.assertIn('recursion_limit', network_code)
        compile(network_code, '<network-example>', 'exec')
        compile(code_text(revised['sec05']['blocks'][6]), '<swarm-example>', 'exec')

    def test_all_imported_references_are_external_and_cover_each_topic(self):
        self.assertEqual(len(self.imported), 24)
        for slide in self.imported:
            with self.subTest(slide=slide['title']):
                self.assertTrue(slide['sources'])
                self.assertLessEqual(len(slide['sources']), 3)
                for key in slide['sources']:
                    label, url = SOURCES[key]
                    self.assertTrue(url.startswith('https://'), url)
                    self.assertNotIn('导入文档', label)
        protocols = [slide for slide in self.imported if slide['source_section'] == 'sec09']
        self.assertEqual(len(protocols), 2)
        details = protocols[1]
        approval = next(slide for slide in self.imported
                        if slide['source_section'] == 'sec08' and '门禁' in slide['title'])
        self.assertEqual(details['sources'], ['collab_a2a', 'collab_mcp_server', 'collab_mcp'])
        self.assertIn('meta_team', approval['sources'])

    def test_removal_preserves_remaining_time_and_outing_demos(self):
        self.assertEqual(sum(slide['seconds'] for slide in slides), 5407)
        self.assertEqual(sum(seconds for _, seconds in CHAPTERS), 5407)
        self.assertEqual(sum('outing-slide' in slide['layout'] for slide in slides), 7)
        self.assertEqual(sum('__DIAGNOSIS_LAB__' in slide['body'] for slide in slides), 0)
        removed_seconds = sum(slide['seconds'] for slide in self.original[11:34])
        self.assertEqual(sum(slide['seconds'] for slide in self.imported), removed_seconds - sum(slide['seconds'] for slide in _deleted_slides) + 606)

    def test_source_handlers_are_scoped_to_the_slide_player(self):
        self.assertTrue(self.imported)
        for slide in self.imported:
            self.assertNotIn('onclick=', slide['body'])
            self.assertNotIn('step-nav', slide['body'])
            self.assertNotIn('href="#sec', slide['body'])
        combined = ''.join(slide['body'] for slide in self.imported)
        for hook in ('data-import-accordion',):
            self.assertIn(hook, combined)
        self.assertNotIn('data-import-faq', combined)


if __name__ == '__main__':
    unittest.main()
