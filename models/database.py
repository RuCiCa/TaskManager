import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/tasks.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """建立資料庫連線"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """初始化資料表"""
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            description TEXT,
            publisher TEXT,
            publish_time DATETIME,
            deadline DATETIME,
            status TEXT DEFAULT 'PUBLISHED', -- PUBLISHED, ACCEPTED, COMPLETED, FAILED
            task_type TEXT,                  -- COUNTING, TIMING
            frequency TEXT,                 -- ONCE, PERIODIC
            
            -- 計數型專用
            target_count INTEGER DEFAULT 0,
            current_count INTEGER DEFAULT 0,
            
            -- 計時型專用 (以秒為單位儲存)
            total_seconds INTEGER DEFAULT 0,
            remaining_seconds INTEGER DEFAULT 0,
            
            completed_at DATETIME
        )
        """
        with self.get_connection() as conn:
            conn.execute(query)
            conn.commit()

    def add_task(self, task_data):
        """
        新增任務
        task_data: 字典格式，包含所有必要的欄位
        """
        sql = """
        INSERT INTO tasks (
            title, content, description, publisher, publish_time, 
            deadline, task_type, frequency, target_count, current_count, 
            total_seconds, remaining_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            task_data.get('title'),
            task_data.get('content'),
            task_data.get('description'),
            task_data.get('publisher'),
            task_data.get('publish_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            task_data.get('deadline'),
            task_data.get('task_type'),
            task_data.get('frequency'),
            task_data.get('target_count', 0),
            0, # current_count 初始值
            task_data.get('total_seconds', 0),
            task_data.get('total_seconds', 0) # remaining 初始等於 total
        )
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid

    def get_all_tasks(self):
        """取得所有任務（用於主介面顯示）"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row # 讓結果可以像字典一樣存取
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY publish_time DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_task_by_id(self, task_id):
        """根據 ID 取得單一任務資料"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_task_status(self, task_id, status):
        """更新任務狀態 (接受、完成、失敗)"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == 'COMPLETED' else None
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, now, task_id)
            )

    def update_progress(self, task_id, current_count=None, remaining_seconds=None):
        """更新任務進度"""
        if current_count is not None:
            query = "UPDATE tasks SET current_count = ? WHERE id = ?"
            val = current_count
        else:
            query = "UPDATE tasks SET remaining_seconds = ? WHERE id = ?"
            val = remaining_seconds
            
        with self.get_connection() as conn:
            conn.execute(query, (val, task_id))