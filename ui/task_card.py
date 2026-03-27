from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class TaskCard(QFrame):
    def __init__(self, task_obj, manager, parent=None):
        super().__init__(parent)
        self.task = task_obj
        self.manager = manager
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        
        # 1. 標題與狀態
        title_row = QHBoxLayout()
        self.title_label = QLabel(f"<b>{self.task.title}</b>")
        
        status_colors = {
            'PUBLISHED': '#f9e2af',
            'ACCEPTED': '#89dceb',
            'COMPLETED': '#a6e3a1',
            'FAILED': '#f38ba8'
        }
        color = status_colors.get(self.task.status, '#cdd6f4')
        self.status_label = QLabel(f"<b style='color: {color};'>[{self.task.status}]</b>")
        
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_row.addWidget(self.status_label)
        self.main_layout.addLayout(title_row)

        # 2. 內容
        self.content_label = QLabel(self.task.content)
        self.content_label.setWordWrap(True)
        self.main_layout.addWidget(self.content_label)

        # 3. 進度/時間顯示區
        self.progress_label = QLabel("")
        self.main_layout.addWidget(self.progress_label)
        
        # 4. 功能按鈕區
        self.btn_layout = QHBoxLayout()
        self.setup_buttons()
        self.main_layout.addLayout(self.btn_layout)

        self.setLayout(self.main_layout)
        self.update_ui_display()

    def setup_buttons(self):
        """根據狀態建立按鈕"""
        # 先清除舊按鈕
        for i in reversed(range(self.btn_layout.count())): 
            self.btn_layout.itemAt(i).widget().setParent(None)

        if self.task.status == 'PUBLISHED':
            btn_accept = QPushButton("接受任務")
            btn_accept.clicked.connect(self.on_accept)
            self.btn_layout.addWidget(btn_accept)
            
        elif self.task.status == 'ACCEPTED':
            if hasattr(self.task, 'target_count'): # 計數型
                btn_inc = QPushButton("完成一次 (+1)")
                btn_inc.clicked.connect(self.on_increment)
                self.btn_layout.addWidget(btn_inc)

    def update_ui_display(self):
        """更新文字顯示（計時器每秒會呼叫這個）"""
        if self.task.status == 'ACCEPTED':
            if hasattr(self.task, 'target_count'): # 計數型
                self.progress_label.setText(f"📊 進度: {self.task.progress_text}")
            elif hasattr(self.task, 'total_seconds'): # 計時型
                self.progress_label.setText(f"⏳ 剩餘時間: {self.task.time_left_text}")
        else:
            self.progress_label.setText("")

    def on_accept(self):
        self.manager.accept_task(self.task.id)
        # 接受後通知主視窗刷新，才會切換按鈕
        self.window().refresh_tasks()

    def on_increment(self):
        if self.manager.increment_counting_task(self.task.id):
            self.update_ui_display()
            # 如果因為這次點擊而完成了，刷新列表
            if self.task.status == 'COMPLETED':
                self.window().refresh_tasks()