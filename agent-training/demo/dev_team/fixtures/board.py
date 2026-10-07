"""Task board domain implementation; fixed baseline for the classroom PR."""
import sqlite3

STATUSES = ('todo', 'doing', 'done')


class TaskStore:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(str(db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('CREATE TABLE IF NOT EXISTS tasks '
                                '(id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL)')
        self.connection.commit()

    def create_task(self, title):
        title = title.strip()
        if not title or len(title) > 120:
            raise ValueError('标题不能为空，且不能超过120字')
        cursor = self.connection.execute('INSERT INTO tasks(title, status) VALUES (?, ?)', (title, 'todo'))
        self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM tasks WHERE id = ?', (cursor.lastrowid,)).fetchone())

    def list_tasks(self):
        return [dict(row) for row in self.connection.execute('SELECT * FROM tasks ORDER BY id')]

    def update_status(self, task_id, status):
        status = status.strip()
        if status not in STATUSES:
            raise ValueError('不允许的任务状态')
        cursor = self.connection.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        if cursor.rowcount != 1:
            raise KeyError(task_id)
        self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone())

    def close(self):
        self.connection.close()
