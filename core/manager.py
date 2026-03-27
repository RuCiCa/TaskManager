from models.database import DatabaseManager
from models.task import CountingTask, TimingTask
from datetime import datetime

class TaskManager:
    def __init__(self):
        self.db = DatabaseManager()

    def _create_task_instance(self, data):
        if data['task_type'] == 'COUNTING':
            return CountingTask(data)
        elif data['task_type'] == 'TIMING':
            return TimingTask(data)
        return None

    def publish_new_task(self, task_info):
        return self.db.add_task(task_info)

    def get_all_tasks(self, status_filter=None):
        raw_tasks = self.db.get_all_tasks()
        task_objects = []
        for data in raw_tasks:
            obj = self._create_task_instance(data)
            if not obj: continue
            if status_filter:
                if obj.status in status_filter:
                    task_objects.append(obj)
            else:
                task_objects.append(obj)
        return task_objects

    def get_history_tasks(self):
        return self.get_all_tasks(status_filter=['COMPLETED', 'FAILED'])

    def accept_task(self, task_id):
        self.db.update_task_status(task_id, 'ACCEPTED')

    def complete_task(self, task_id):
        """完成任務並處理週期性邏輯"""
        # 1. 更新原任務狀態為已完成
        self.db.update_task_status(task_id, 'COMPLETED')
        
        # 2. 檢查是否為週期性任務
        task_data = self.db.get_task_by_id(task_id)
        if task_data and task_data['frequency'] == 'PERIODIC':
            # 建立一個新任務副本
            new_task = {
                'title': task_data['title'],
                'content': task_data['content'],
                'description': task_data['description'],
                'publisher': task_data['publisher'],
                'task_type': task_data['task_type'],
                'frequency': task_data['frequency'],
                'target_count': task_data['target_count'],
                'total_seconds': task_data['total_seconds'],
                'publish_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # 重新發布
            self.db.add_task(new_task)

    def increment_counting_task(self, task_id):
        all_tasks = self.db.get_all_tasks()
        target_data = next((t for t in all_tasks if t['id'] == task_id), None)
        
        if target_data:
            task_obj = CountingTask(target_data)
            if task_obj.increment():
                self.db.update_progress(task_id, current_count=task_obj.current_count)
                if task_obj.status == 'COMPLETED':
                    self.complete_task(task_id) # 使用新的完成邏輯
                return True
        return False

    def update_timing_task(self, task_id, remaining_seconds):
        self.db.update_progress(task_id, remaining_seconds=remaining_seconds)
        if remaining_seconds <= 0:
            self.complete_task(task_id) # 使用新的完成邏輯

    def get_statistics(self):
        tasks = self.db.get_all_tasks()
        total = len(tasks)
        completed = len([t for t in tasks if t['status'] == 'COMPLETED'])
        failed = len([t for t in tasks if t['status'] == 'FAILED'])
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }