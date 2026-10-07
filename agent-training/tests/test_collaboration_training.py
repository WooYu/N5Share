"""Teaching contract: actual source and VS Code runs in the five-pattern span."""
import _bootstrap
import inspect
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'demo'))


class CollaborationTrainingTests(unittest.TestCase):
    def test_pattern_span_is_followed_by_frameworks_then_development_team(self):
        from content import slides
        self.assertEqual(len(slides), 39)
        self.assertIn('雨天出游', slides[13]['title'])
        expected = ['Sequential Chain', 'Supervisor', 'Hierarchical', 'Swarm', 'Network']
        for offset, pattern in enumerate(expected):
            self.assertIn(pattern, slides[14]['body'])
            self.assertIn(pattern, slides[16 + offset]['title'])
            self.assertIn('代码示例', slides[16 + offset]['title'])
        self.assertIn('Microsoft Agent Framework', slides[21]['title'])
        self.assertIn('LangGraph', slides[22]['title'])
        self.assertIn('MetaGPT', slides[23]['title'])
        self.assertEqual(slides[24]['title'], '实战案例：智能软件开发团队')
        self.assertEqual(sum(slide['seconds'] for slide in slides), 5407)

    def test_legacy_reference_playback_remains_separate(self):
        from collaboration_training import lesson_data, PATTERN_ORDER
        from collaboration_patterns import run_demo
        for pattern in PATTERN_ORDER:
            for scenario in ('normal', 'missing'):
                with self.subTest(pattern=pattern, scenario=scenario):
                    actual = lesson_data()[pattern]['traces'][scenario]
                    expected = run_demo(pattern, scenario=scenario)
                    self.assertEqual(actual['status'], expected['status'])
                    self.assertEqual(actual['events'], expected['events'])
                    self.assertEqual(actual['state'], expected['state'])
        self.assertEqual(lesson_data()['sequential']['traces']['missing']['status'], 'needs_input')
        for pattern in PATTERN_ORDER[1:]:
            self.assertEqual(lesson_data()[pattern]['traces']['missing']['status'], 'completed')

    def test_active_pages_use_real_graph_source_and_live_runner(self):
        from content import slides
        from collaboration_vscode import PATTERNS, source_excerpt
        from html import unescape
        for offset, pattern in enumerate(PATTERNS):
            body = slides[16 + offset]['body']
            source = (ROOT / 'demo/collaboration_live' / (pattern + '.py')).read_text(encoding='utf-8')
            excerpt = unescape(source_excerpt(pattern).split('<code>')[1].split('</code>')[0])
            self.assertIn(excerpt, source)
            self.assertIn('run_collaboration.py --pattern ' + pattern, slides[16 + offset]['notes'])
            self.assertNotIn('run_collaboration.py', body)
            self.assertNotIn('data-ct-data', body)
        self.assertNotIn('真实模型配置 · DeepSeek 主用，OpenAI 备用', [slide['title'] for slide in slides])


if __name__ == '__main__':
    unittest.main()
