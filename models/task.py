from datetime import datetime

class Task:
    """任務基底類別"""
    def __init__(self, data):
        self.id = data.get('id')
        self.title = data.get('title')
        self.content = data.get('content')
        self.description = data.get('description')
        self.publisher = data.get('publisher')
        self.publish_time = data.get('publish_time')
        self.deadline = data.get('deadline')
        self.status = data.get('status', 'PUBLISHED')  # PUBLISHED, ACCEPTED, COMPLETED, FAILED
        self.frequency = data.get('frequency', 'ONCE') # ONCE, PERIODIC

    def accept(self):
        """接受任務"""
        if self.status == 'PUBLISHED':
            self.status = 'ACCEPTED'
            return True
        return False

    def fail(self):
        """標記為失敗"""
        self.status = 'FAILED'

    def __repr__(self):
        return f"<{self.__class__.__name__} ID:{self.id} Title:{self.title} Status:{self.status}>"


class CountingTask(Task):
    """計數型任務"""
    def __init__(self, data):
        super().__init__(data)
        self.target_count = data.get('target_count', 0)
        self.current_count = data.get('current_count', 0)

    def increment(self):
        """進度 +1"""
        if self.status == 'ACCEPTED' and self.current_count < self.target_count:
            self.current_count += 1
            if self.current_count >= self.target_count:
                self.status = 'COMPLETED'
            return True
        return False

    @property
    def progress_text(self):
        """回傳進度文字，例如: 2/5"""
        return f"{self.current_count}/{self.target_count}"


class TimingTask(Task):
    """計時型任務"""
    def __init__(self, data):
        super().__init__(data)
        self.total_seconds = data.get('total_seconds', 0)
        self.remaining_seconds = data.get('remaining_seconds', 0)

    def tick(self, seconds=1):
        """時間倒數"""
        if self.status == 'ACCEPTED' and self.remaining_seconds > 0:
            self.remaining_seconds -= seconds
            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                self.status = 'COMPLETED'
            return True
        return False

    @property
    def time_left_text(self):
        """將秒數轉為 MM:SS 格式"""
        mins, secs = divmod(self.remaining_seconds, 60)
        return f"{mins:02d}:{secs:02d}"