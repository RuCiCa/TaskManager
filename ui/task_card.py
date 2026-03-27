from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import Qt

class TaskCard(QFrame):
    def __init__(self, task_obj, manager, parent=None):
        super().__init__(parent)
        self.task = task_obj
        self.manager = manager
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(2)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 標題與狀態
        title_row = QHBoxLayout()
        title_label = QLabel(f"<b>{self.task.title}</b>")
        status_label = QLabel(f"[{self.task.status}]")
        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(status_label)
        layout.addLayout(title_row)

        # 描述
        desc_label = QLabel(self.task.content)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 進度顯示 (計數型或計時型)
        if self.task.status == 'ACCEPTED':
            if hasattr(self.task, 'target_count'): # 計數型
                self.progress = QLabel(f"進度: {self.task.progress_text}")
                layout.addWidget(self.progress)
                
                btn_inc = QPushButton("完成一次 (+1)")
                btn_inc.clicked.connect(self.on_increment)
                layout.addWidget(btn_inc)
            
            elif hasattr(self.task, 'total_seconds'): # 計時型
                self.time_label = QLabel(f"剩餘時間: {self.task.time_left_text}")
                layout.addWidget(self.time_label)
                # 計時器的 UI 邏輯可以之後在 Main 裡面跑，這裡先留顯示

        # 功能按鈕
        btn_layout = QHBoxLayout()
        if self.task.status == 'PUBLISHED':
            btn_accept = QPushButton("接受任務")
            btn_accept.clicked.connect(self.on_accept)
            btn_layout.addWidget(btn_accept)
            
            btn_reject = QPushButton("拒絕")
            btn_layout.addWidget(btn_reject)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_accept(self):
        self.manager.accept_task(self.task.id)
        # 這裡之後會呼叫父視窗重新整理介面
        print(f"任務 {self.task.id} 已接受")

    def on_increment(self):
        if self.manager.increment_counting_task(self.task.id):
            print(f"任務 {self.task.id} 進度更新")