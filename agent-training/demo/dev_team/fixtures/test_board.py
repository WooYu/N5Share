"""Trusted acceptance tests. The developer cannot change this file."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('candidate_board', Path(__file__).with_name('board.py'))
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)


class BoardAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'tasks.db'
        self.store = board.TaskStore(self.db)
        self.addCleanup(lambda: self.store.close())

    def test_create_and_list(self):
        task = self.store.create_task('  学会代码评审  ')
        self.assertEqual(task['title'], '学会代码评审')
        self.assertEqual(task['status'], 'todo')
        self.assertEqual(self.store.list_tasks(), [task])

    def test_empty_and_long_titles_are_rejected(self):
        for title in ('', '   ', 'x' * 121):
            with self.subTest(title=title), self.assertRaises(ValueError):
                self.store.create_task(title)

    def test_valid_status_survives_reopen(self):
        task = self.store.create_task('测试持久化')
        self.store.update_status(task['id'], 'done')
        self.store.close()
        self.store = board.TaskStore(self.db)
        self.assertEqual(self.store.list_tasks()[0]['status'], 'done')

    def test_invalid_status_is_rejected(self):
        task = self.store.create_task('保持状态契约')
        for status in ('deleted', '', 'DONE'):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.store.update_status(task['id'], status)
            self.assertEqual(self.store.list_tasks()[0]['status'], 'todo')

    def test_missing_task_is_rejected(self):
        with self.assertRaises(KeyError):
            self.store.update_status(999, 'done')


if __name__ == '__main__':
    unittest.main()
