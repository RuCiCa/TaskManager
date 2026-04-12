from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QSpinBox, QPushButton,
                             QTimeEdit, QDateTimeEdit, QCheckBox, QButtonGroup,
                             QWidget, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime


class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(460)
        self._manager = getattr(parent, 'manager', None) if parent else None
        self._drag_offset = None
        self.init_ui()

    # ── 拖動支援 ───────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and self._drag_offset is not None:
            self.move(e.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_offset = None
        super().mouseReleaseEvent(e)

    # ── UI 建構 ────────────────────────────────────────────────

    def init_ui(self):
        # 最外層透明 layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # 可見容器
        container = QWidget()
        container.setObjectName("DialogContainer")
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(8)

        # ── 自訂標題列 ──
        title_bar = QHBoxLayout()
        title_lbl = QLabel("📋 發布新任務")
        title_lbl.setObjectName("DialogTitle")
        close_btn = QPushButton("✖")
        close_btn.setObjectName("DialogClose")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(title_lbl)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        layout.addLayout(title_bar)

        # ── 基本資訊 ──
        layout.addWidget(self._section("基本資訊"))
        layout.addWidget(QLabel("任務標題："))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("任務內容簡述："))
        self.content_input = QLineEdit()
        layout.addWidget(self.content_input)

        layout.addWidget(QLabel("詳細說明："))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(65)
        layout.addWidget(self.desc_input)

        # ── 任務設定 ──
        layout.addWidget(self._section("任務設定"))

        # 類型
        type_row = QHBoxLayout()
        type_row.addWidget(self._row_label("類型："))
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        for i, (text, oid) in enumerate([("🔢 計數型", "TypeBtn"), ("⏱ 計時型", "TypeBtn")]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName(oid)
            if i == 0:
                btn.setChecked(True)
            self.type_group.addButton(btn, i)
            type_row.addWidget(btn)
        type_row.addStretch()
        self.type_group.idClicked.connect(self._on_type_changed)
        layout.addLayout(type_row)

        # 頻率
        freq_row = QHBoxLayout()
        freq_row.addWidget(self._row_label("頻率："))
        self.freq_group = QButtonGroup(self)
        self.freq_group.setExclusive(True)
        for i, (text, oid) in enumerate([("🔂 單次", "FreqBtn"), ("🔁 週期", "FreqBtn")]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName(oid)
            if i == 0:
                btn.setChecked(True)
            self.freq_group.addButton(btn, i)
            freq_row.addWidget(btn)
        freq_row.addStretch()
        layout.addLayout(freq_row)

        # 難度
        diff_row = QHBoxLayout()
        diff_row.addWidget(self._row_label("難度："))
        self.diff_group = QButtonGroup(self)
        self.diff_group.setExclusive(True)
        diff_cfg = [("簡單", "DiffEasy", False), ("中等", "DiffMedium", True), ("困難", "DiffHard", False)]
        for i, (text, oid, checked) in enumerate(diff_cfg):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName(oid)
            btn.setChecked(checked)
            self.diff_group.addButton(btn, i)
            diff_row.addWidget(btn)
        diff_row.addStretch()
        layout.addLayout(diff_row)

        # ── 目標設定 ──
        layout.addWidget(self._section("目標設定"))

        # 計數型欄位
        self.count_frame = QWidget()
        count_row = QHBoxLayout(self.count_frame)
        count_row.setContentsMargins(0, 0, 0, 0)
        count_row.addWidget(QLabel("🔢  目標次數："))
        self.target_count_input = QSpinBox()
        self.target_count_input.setRange(1, 9999)
        self.target_count_input.setMinimumHeight(34)
        count_row.addWidget(self.target_count_input)
        count_row.addStretch()
        layout.addWidget(self.count_frame)

        # 計時型欄位
        self.time_frame = QWidget()
        time_row = QHBoxLayout(self.time_frame)
        time_row.setContentsMargins(0, 0, 0, 0)
        time_row.addWidget(QLabel("⏱  目標時間："))
        self.target_time_input = QTimeEdit()
        self.target_time_input.setDisplayFormat("HH:mm:ss")
        self.target_time_input.setMinimumHeight(34)
        time_row.addWidget(self.target_time_input)
        time_row.addStretch()
        self.time_frame.setVisible(False)
        layout.addWidget(self.time_frame)

        # ── 截止時間 ──
        dl_row = QHBoxLayout()
        dl_row.addWidget(QLabel("📅"))
        self.deadline_check = QCheckBox("截止時間：")
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.deadline_input.setEnabled(False)
        self.deadline_input.setMinimumHeight(34)
        self.deadline_check.toggled.connect(self.deadline_input.setEnabled)
        dl_row.addWidget(self.deadline_check)
        dl_row.addWidget(self.deadline_input)
        layout.addLayout(dl_row)

        # ── 按鈕列 ──
        btn_row = QHBoxLayout()
        self.ai_btn = QPushButton("✨ AI 幫我規劃")
        self.ai_btn.setObjectName("AiBtn")
        self.ai_btn.clicked.connect(self.on_ai_decompose)
        self.save_btn = QPushButton("✅ 發布任務")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.ai_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    # ── 輔助方法 ───────────────────────────────────────────────

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("SectionLabel")
        return lbl

    def _row_label(self, text):
        lbl = QLabel(text)
        lbl.setFixedWidth(48)
        return lbl

    def _on_type_changed(self, btn_id):
        self.count_frame.setVisible(btn_id == 0)
        self.time_frame.setVisible(btn_id == 1)

    # ── AI 規劃 ────────────────────────────────────────────────

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
                self.reject()

        except Exception as e:
            QMessageBox.critical(self, "AI 錯誤", f"呼叫 AI 時發生錯誤：\n{e}")
        finally:
            self.ai_btn.setEnabled(True)
            self.ai_btn.setText("✨ AI 幫我規劃")

    # ── 取得資料 ───────────────────────────────────────────────

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
            'task_type': ['COUNTING', 'TIMING'][self.type_group.checkedId()],
            'frequency': ['ONCE', 'PERIODIC'][self.freq_group.checkedId()],
            'difficulty': ['EASY', 'MEDIUM', 'HARD'][self.diff_group.checkedId()],
            'target_count': self.target_count_input.value(),
            'total_seconds': total_seconds,
            'deadline': deadline,
        }
