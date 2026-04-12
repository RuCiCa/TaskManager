import winsound
import threading
from datetime import datetime
from models.database import DatabaseManager, DIFFICULTY_EXP
from models.task import CountingTask, TimingTask


def _beep_async(freq, duration):
    """在背景執行緒播放嗶聲，避免阻塞 UI"""
    threading.Thread(target=winsound.Beep, args=(freq, duration), daemon=True).start()


def play_sound_complete():
    _beep_async(880, 200)


def play_sound_levelup():
    def _seq():
        winsound.Beep(523, 150)
        winsound.Beep(659, 150)
        winsound.Beep(784, 300)
    threading.Thread(target=_seq, daemon=True).start()


def play_sound_fail():
    _beep_async(220, 500)


class TaskManager:
    def __init__(self):
        self.db = DatabaseManager()

    def _create_task_instance(self, data):
        if data['task_type'] == 'COUNTING':
            return CountingTask(data)
        elif data['task_type'] == 'TIMING':
            return TimingTask(data)
        return None

    # ── 基本任務操作 ───────────────────────────────────────────

    def publish_new_task(self, task_info):
        return self.db.add_task(task_info)

    def get_all_tasks(self, status_filter=None):
        task_objects = []
        for data in self.db.get_all_tasks():
            obj = self._create_task_instance(data)
            if not obj:
                continue
            if status_filter is None or obj.status in status_filter:
                task_objects.append(obj)
        return task_objects

    def get_history_tasks(self):
        return self.get_all_tasks(status_filter=['COMPLETED', 'FAILED'])

    def accept_task(self, task_id):
        self.db.update_task_status(task_id, 'ACCEPTED')

    def fail_task(self, task_id):
        self.db.update_task_status(task_id, 'FAILED')
        play_sound_fail()

    def complete_task(self, task_id):
        """完成任務，處理週期性複製、EXP、成就，回傳結果 dict。"""
        self.db.update_task_status(task_id, 'COMPLETED')
        play_sound_complete()

        task_data = self.db.get_task_by_id(task_id)
        result = {'leveled_up': False, 'new_level': 1, 'exp_gained': 0, 'new_achievements': []}

        # 週期性任務：複製並重新發布
        if task_data and task_data['frequency'] == 'PERIODIC':
            new_task = {k: task_data[k] for k in (
                'title', 'content', 'description', 'publisher',
                'task_type', 'frequency', 'difficulty',
                'target_count', 'total_seconds',
            )}
            new_task['publish_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.add_task(new_task)

        # EXP 獎勵
        if task_data:
            exp = DIFFICULTY_EXP.get(task_data.get('difficulty', 'MEDIUM'), 25)
            leveled_up, new_level = self.db.update_exp(exp)
            result.update({'leveled_up': leveled_up, 'new_level': new_level, 'exp_gained': exp})

            if leveled_up:
                play_sound_levelup()
                # 成就：Lv.5
                if new_level >= 5:
                    ach = self.db.unlock_achievement('level_5')
                    if ach:
                        result['new_achievements'].append(ach)

        # 成就檢查：完成次數
        completed_count = len([t for t in self.db.get_all_tasks() if t['status'] == 'COMPLETED'])
        milestones = [(1, 'first_complete'), (5, 'five_complete'), (10, 'ten_complete')]
        for threshold, key in milestones:
            if completed_count >= threshold:
                ach = self.db.unlock_achievement(key)
                if ach:
                    result['new_achievements'].append(ach)

        # 成就：首次完成週期性任務
        if task_data and task_data['frequency'] == 'PERIODIC':
            ach = self.db.unlock_achievement('first_periodic')
            if ach:
                result['new_achievements'].append(ach)

        return result

    # ── 進度更新 ───────────────────────────────────────────────

    def increment_counting_task(self, task_id):
        """計數 +1，若完成則觸發 complete_task。回傳 (incremented, complete_result)。"""
        target_data = self.db.get_task_by_id(task_id)
        if not target_data:
            return False, None

        task_obj = CountingTask(target_data)
        if task_obj.increment():
            self.db.update_progress(task_id, current_count=task_obj.current_count)
            if task_obj.status == 'COMPLETED':
                return True, self.complete_task(task_id)
            return True, None
        return False, None

    def update_timing_task(self, task_id, remaining_seconds):
        """更新計時剩餘秒數，歸零時觸發 complete_task。回傳 complete_result 或 None。"""
        self.db.update_progress(task_id, remaining_seconds=remaining_seconds)
        if remaining_seconds <= 0:
            return self.complete_task(task_id)
        return None

    # ── 截止時間檢查 ───────────────────────────────────────────

    def check_deadlines(self):
        """檢查所有進行中任務的截止時間，自動標記過期者為 FAILED。回傳被 fail 的 id 列表。"""
        now = datetime.now()
        failed_ids = []
        for data in self.db.get_all_tasks():
            if data['status'] not in ('PUBLISHED', 'ACCEPTED'):
                continue
            deadline_str = data.get('deadline')
            if not deadline_str:
                continue
            try:
                deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if now > deadline_dt:
                self.fail_task(data['id'])
                failed_ids.append(data['id'])
        return failed_ids

    # ── 玩家資訊 ───────────────────────────────────────────────

    def get_profile(self):
        return self.db.get_profile()

    def get_all_achievements(self):
        return self.db.get_all_achievements()

    # ── 統計 ───────────────────────────────────────────────────

    def get_statistics(self):
        tasks = self.db.get_all_tasks()
        total = len(tasks)
        completed = sum(1 for t in tasks if t['status'] == 'COMPLETED')
        failed = sum(1 for t in tasks if t['status'] == 'FAILED')
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
        }
