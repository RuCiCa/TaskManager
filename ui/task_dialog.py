from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QComboBox, QSpinBox,
                             QPushButton, QTimeEdit, QDateTimeEdit, QCheckBox,
                             QMessageBox)
from PyQt6.QtCore import QTime, QDateTime

class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("發布新任務")
        self.setMinimumWidth(420)
        self._manager = getattr(parent, 'manager', None) if parent else None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. 基本資訊
        layout.addWidget(QLabel("任務標題:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("任務內容簡述:"))
        self.content_input = QLineEdit()
        layout.addWidget(self.content_input)

        layout.addWidget(QLabel("詳細說明:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)

        # 2. 類型、頻率、難度 (橫向佈局)
        type_layout = QHBoxLayout()

        vbox_type = QVBoxLayout()
        vbox_type.addWidget(QLabel("任務類型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["COUNTING", "TIMING"])
        self.type_combo.currentTextChanged.connect(self.toggle_type_fields)
        vbox_type.addWidget(self.type_combo)
        type_layout.addLayout(vbox_type)

        vbox_freq = QVBoxLayout()
        vbox_freq.addWidget(QLabel("頻率:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["ONCE", "PERIODIC"])
        vbox_freq.addWidget(self.freq_combo)
        type_layout.addLayout(vbox_freq)

        vbox_diff = QVBoxLayout()
        vbox_diff.addWidget(QLabel("難度:"))
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["EASY", "MEDIUM", "HARD"])
        self.diff_combo.setCurrentText("MEDIUM")
        vbox_diff.addWidget(self.diff_combo)
        type_layout.addLayout(vbox_diff)

        layout.addLayout(type_layout)

        # 3. 動態欄位：計數型 vs 計時型
        self.count_widget = QLabel("目標次數:")
        self.target_count_input = QSpinBox()
        self.target_count_input.setRange(1, 9999)

        self.time_widget = QLabel("目標時間 (HH:MM:SS):")
        self.target_time_input = QTimeEdit()
        self.target_time_input.setDisplayFormat("HH:mm:ss")
        self.target_time_input.setHidden(True)
        self.time_widget.setHidden(True)

        layout.addWidget(self.count_widget)
        layout.addWidget(self.target_count_input)
        layout.addWidget(self.time_widget)
        layout.addWidget(self.target_time_input)

        # 4. 截止時間 (可選)
        deadline_row = QHBoxLayout()
        self.deadline_check = QCheckBox("設定截止時間:")
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.deadline_input.setEnabled(False)
        self.deadline_check.toggled.connect(self.deadline_input.setEnabled)
        deadline_row.addWidget(self.deadline_check)
        deadline_row.addWidget(self.deadline_input)
        layout.addLayout(deadline_row)

        # 5. 按鈕區 (AI 規劃 + 發布 + 取消)
        btn_layout = QHBoxLayout()
        self.ai_btn = QPushButton("✨ AI 幫我規劃")
        self.ai_btn.clicked.connect(self.on_ai_decompose)
        self.save_btn = QPushButton("發布任務")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ai_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_type_fields(self, task_type):
        is_counting = (task_type == "COUNTING")
        self.count_widget.setVisible(is_counting)
        self.target_count_input.setVisible(is_counting)
        self.time_widget.setVisible(not is_counting)
        self.target_time_input.setVisible(not is_counting)

    def on_ai_decompose(self):
        goal = self.title_input.text().strip()
        if not goal:
            QMessageBox.warning(self, "提示", "請先在「任務標題」輸入你的目標，再讓 AI 幫你規劃。")
            return

        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("AI 思考中...")

        try:
            from core.ai_assistant import decompose_task
            tasks = decompose_task(goal)

            if not tasks:
                QMessageBox.warning(self, "AI 錯誤", "AI 未回傳任何任務，請稍後再試。")
                return

            # 組建預覽文字
            lines = [f"AI 為你規劃了 {len(tasks)} 個子任務：\n"]
            for i, t in enumerate(tasks, 1):
                lines.append(f"{i}. 【{t.get('difficulty','MEDIUM')}】{t['title']}")
                if t.get('content'):
                    lines.append(f"   {t['content']}")
            lines.append("\n確定後將批次發布這些任務（目前彈窗不會另外發布）。")

            reply = QMessageBox.question(self, "AI 任務規劃結果", "\n".join(lines),
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes and self._manager:
                for t in tasks:
                    self._manager.publish_new_task(t)
                QMessageBox.information(self, "完成", f"已批次發布 {len(tasks)} 個任務！")
                self.reject()  # 關閉彈窗，讓主視窗刷新

        except Exception as e:
            QMessageBox.critical(self, "AI 錯誤", f"呼叫 AI 時發生錯誤：\n{e}")
        finally:
            self.ai_btn.setEnabled(True)
            self.ai_btn.setText("✨ AI 幫我規劃")

    def get_data(self):
        qtime = self.target_time_input.time()
        total_seconds = qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()

        deadline = None
        if self.deadline_check.isChecked():
            deadline = self.deadline_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        return {
            'title': self.title_input.text(),
            'content': self.content_input.text(),
            'description': self.desc_input.toPlainText(),
            'publisher': 'Me',
            'task_type': self.type_combo.currentText(),
            'frequency': self.freq_combo.currentText(),
            'difficulty': self.diff_combo.currentText(),
            'target_count': self.target_count_input.value(),
            'total_seconds': total_seconds,
            'deadline': deadline,
        }
