import sqlite3
from datetime import datetime

# EXP 獎勵對照表
DIFFICULTY_EXP = {'EASY': 10, 'MEDIUM': 25, 'HARD': 50}

# 預設成就清單
DEFAULT_ACHIEVEMENTS = [
    ('first_complete',  '初出茅廬', '完成你的第一個任務'),
    ('five_complete',   '漸入佳境', '累計完成 5 個任務'),
    ('ten_complete',    '任務達人', '累計完成 10 個任務'),
    ('first_periodic',  '持之以恆', '完成第一個週期性任務'),
    ('level_5',         '冒險者',   '角色等級達到 Lv.5'),
]


class DatabaseManager:
    def __init__(self, db_path="data/tasks.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            # --- tasks 表 ---
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                description TEXT,
                publisher TEXT,
                publish_time DATETIME,
                deadline DATETIME,
                status TEXT DEFAULT 'PUBLISHED',
                task_type TEXT,
                frequency TEXT,
                difficulty TEXT DEFAULT 'MEDIUM',
                target_count INTEGER DEFAULT 0,
                current_count INTEGER DEFAULT 0,
                total_seconds INTEGER DEFAULT 0,
                remaining_seconds INTEGER DEFAULT 0,
                completed_at DATETIME
            )""")

            # 為舊資料庫補上 difficulty 欄位（若已存在會靜默忽略）
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN difficulty TEXT DEFAULT 'MEDIUM'")
            except sqlite3.OperationalError:
                pass

            # --- user_profile 表 ---
            conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY DEFAULT 1,
                level INTEGER DEFAULT 1,
                current_exp INTEGER DEFAULT 0,
                total_exp INTEGER DEFAULT 0
            )""")
            conn.execute("INSERT OR IGNORE INTO user_profile (id) VALUES (1)")

            # --- achievements 表 ---
            conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unlocked_at DATETIME
            )""")
            for key, name, desc in DEFAULT_ACHIEVEMENTS:
                conn.execute(
                    "INSERT OR IGNORE INTO achievements (key, name, description) VALUES (?, ?, ?)",
                    (key, name, desc)
                )
            conn.commit()

    # ── 任務 CRUD ──────────────────────────────────────────────

    def add_task(self, task_data):
        sql = """
        INSERT INTO tasks (
            title, content, description, publisher, publish_time,
            deadline, task_type, frequency, difficulty,
            target_count, current_count, total_seconds, remaining_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            task_data.get('difficulty', 'MEDIUM'),
            task_data.get('target_count', 0),
            0,
            task_data.get('total_seconds', 0),
            task_data.get('total_seconds', 0),
        )
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid

    def get_all_tasks(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY publish_time DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_task_by_id(self, task_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_task_status(self, task_id, status):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == 'COMPLETED' else None
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, now, task_id)
            )

    def update_progress(self, task_id, current_count=None, remaining_seconds=None):
        if current_count is not None:
            query = "UPDATE tasks SET current_count = ? WHERE id = ?"
            val = current_count
        else:
            query = "UPDATE tasks SET remaining_seconds = ? WHERE id = ?"
            val = remaining_seconds
        with self.get_connection() as conn:
            conn.execute(query, (val, task_id))

    # ── 玩家檔案 ───────────────────────────────────────────────

    def get_profile(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
            return dict(row)

    def update_exp(self, gained_exp):
        """增加 EXP，自動處理升級。回傳 (leveled_up: bool, new_level: int)"""
        profile = self.get_profile()
        level = profile['level']
        current_exp = profile['current_exp'] + gained_exp
        total_exp = profile['total_exp'] + gained_exp
        leveled_up = False

        # 升級門檻：level * 100
        while current_exp >= level * 100:
            current_exp -= level * 100
            level += 1
            leveled_up = True

        with self.get_connection() as conn:
            conn.execute(
                "UPDATE user_profile SET level=?, current_exp=?, total_exp=? WHERE id=1",
                (level, current_exp, total_exp)
            )
        return leveled_up, level

    # ── 成就 ───────────────────────────────────────────────────

    def unlock_achievement(self, key):
        """解鎖成就。若已解鎖回傳 False，首次解鎖回傳成就資料 dict。"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM achievements WHERE key=?", (key,)
            ).fetchone()
            if not row or row['unlocked_at']:
                return False
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "UPDATE achievements SET unlocked_at=? WHERE key=?", (now, key)
            )
            return dict(row)

    def get_all_achievements(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM achievements").fetchall()
            return [dict(r) for r in rows]
