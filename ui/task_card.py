from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
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
        freq_tag = " [重置]" if self.task.frequency == "PERIODIC" else ""
        self.title_label = QLabel(f"<b>{self.task.title}{freq_tag}</b>")

        status_colors = {
            'PUBLISHED': '#f9e2af',
            'ACCEPTED':  '#89dceb',
            'COMPLETED': '#a6e3a1',
            'FAILED':    '#f38ba8',
        }
        color = status_colors.get(self.task.status, '#cdd6f4')
        self.status_label = QLabel(f"<b style='color: {color};'>[{self.task.status}]</b>")

        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_row.addWidget(self.status_label)
        self.main_layout.addLayout(title_row)

        # 2. 內容
        self.content_label = QLabel(self.task.content or '')
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
        for i in reversed(range(self.btn_layout.count())):
            widget = self.btn_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.task.status == 'PUBLISHED':
            btn_accept = QPushButton("接受任務")
            btn_accept.clicked.connect(self.on_accept)
            self.btn_layout.addWidget(btn_accept)

        elif self.task.status == 'ACCEPTED':
            if hasattr(self.task, 'target_count'):
                btn_inc = QPushButton("完成一次 (+1)")
                btn_inc.clicked.connect(self.on_increment)
                self.btn_layout.addWidget(btn_inc)

        elif self.task.status == 'FAILED':
            btn_ai = QPushButton("💬 AI 怎麼說")
            btn_ai.clicked.connect(self.on_ai_coach)
            self.btn_layout.addWidget(btn_ai)

    def update_ui_display(self):
        if self.task.status == 'ACCEPTED':
            if hasattr(self.task, 'target_count'):
                self.progress_label.setText(f"進度: {self.task.progress_text}")
            elif hasattr(self.task, 'total_seconds'):
                self.progress_label.setText(f"剩餘時間: {self.task.time_left_text}")
        else:
            self.progress_label.setText("")

    def on_accept(self):
        self.manager.accept_task(self.task.id)
        if self.window():
            self.window().refresh_tasks()

    def on_increment(self):
        incremented, result = self.manager.increment_counting_task(self.task.id)
        if incremented:
            self.task.increment()
            self.update_ui_display()

            if self.task.status == 'COMPLETED':
                if self.window() and hasattr(self.window(), '_handle_complete_result'):
                    self.window()._handle_complete_result(result, self.task.title)
                if self.window():
                    self.window().refresh_tasks()

    def on_ai_coach(self):
        try:
            from core.ai_assistant import generate_failure_message
            msg = generate_failure_message(self.task.title or '這個任務')
            QMessageBox.information(self, "AI 教練說：", msg)
        except Exception as e:
            QMessageBox.critical(self, "AI 錯誤", f"呼叫 AI 時發生錯誤：\n{e}")
