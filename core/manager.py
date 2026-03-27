from models.database import DatabaseManager
from models.task import CountingTask, TimingTask

class TaskManager:
    def __init__(self):
        # 初始化資料庫連接
        self.db = DatabaseManager()

    def _create_task_instance(self, data):
        """工廠方法：根據資料庫的類型標籤，建立對應的物件"""
        if data['task_type'] == 'COUNTING':
            return CountingTask(data)
        elif data['task_type'] == 'TIMING':
            return TimingTask(data)
        return None

    def publish_new_task(self, task_info):
        """發布新任務"""
        # task_info 是從 UI 傳過來的字典
        return self.db.add_task(task_info)

    def get_all_tasks(self, status_filter=None):
        """
        獲取所有任務並轉換成物件列表
        status_filter: 可選，例如 ['PUBLISHED', 'ACCEPTED']
        """
        raw_tasks = self.db.get_all_tasks()
        task_objects = []
        
        for data in raw_tasks:
            obj = self._create_task_instance(data)
            if status_filter:
                if obj.status in status_filter:
                    task_objects.append(obj)
            else:
                task_objects.append(obj)
        
        return task_objects

    def accept_task(self, task_id):
        """接受任務邏輯"""
        # 1. 這裡可以加入檢查邏輯（例如是否已有太多進行中的任務）
        self.db.update_task_status(task_id, 'ACCEPTED')

    def increment_counting_task(self, task_id):
        """計數任務進度 +1"""
        # 先從資料庫取出最新狀態
        all_tasks = self.db.get_all_tasks()
        target_data = next((t for t in all_tasks if t['id'] == task_id), None)
        
        if target_data:
            task_obj = CountingTask(target_data)
            if task_obj.increment(): # 執行物件內部的增加邏輯
                # 同步回資料庫
                self.db.update_progress(task_id, current_count=task_obj.current_count)
                # 如果狀態變成了 COMPLETED，也要同步更新狀態
                if task_obj.status == 'COMPLETED':
                    self.db.update_task_status(task_id, 'COMPLETED')
                return True
        return False

    def update_timing_task(self, task_id, remaining_seconds):
        """更新計時任務的剩餘時間"""
        self.db.update_progress(task_id, remaining_seconds=remaining_seconds)
        if remaining_seconds <= 0:
            self.db.update_task_status(task_id, 'COMPLETED')

    def get_statistics(self):
        """獲取簡易統計數據"""
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