from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, QTimer


class AiChatTab(QWidget):
    def __init__(self, manager=None, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.messages = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 說明文字
        hint = QLabel("💬 和 AI 聊任務規劃、進度分析或尋求鼓勵")
        hint.setStyleSheet("color: #585b70; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        # 對話區
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setSpacing(6)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_content)
        layout.addWidget(self.scroll_area)

        # 輸入列
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("輸入訊息，按 Enter 發送...")
        self.input_field.setMinimumHeight(36)
        self.input_field.returnPressed.connect(self.on_send)
        self.send_btn = QPushButton("發送")
        self.send_btn.setFixedWidth(64)
        self.send_btn.clicked.connect(self.on_send)
        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

    def _add_bubble(self, text: str, is_user: bool):
        """在對話區新增一個訊息泡泡"""
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(320)
        bubble.setObjectName("UserBubble" if is_user else "AiBubble")

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        if is_user:
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch()

        # 插入在最後的 stretch 之前
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row_widget)

        # 自動捲到底
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def on_send(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText("...")

        self._add_bubble(text, is_user=True)
        self.messages.append({"role": "user", "content": text})

        try:
            from core.ai_assistant import chat
            response = chat(self.messages)
            self.messages.append({"role": "assistant", "content": response})
            self._add_bubble(response, is_user=False)
        except Exception as e:
            self._add_bubble(f"⚠️ 錯誤：{e}", is_user=False)
        finally:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("發送")
