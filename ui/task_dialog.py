from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QSpinBox, 
                             QPushButton, QTimeEdit)
from PyQt6.QtCore import QTime

class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("發布新任務")
        self.setMinimumWidth(400)
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
        layout.addWidget(self.desc_input)

        # 2. 類型與頻率 (橫向佈局)
        type_layout = QHBoxLayout()
        
        # 任務類型
        vbox_type = QVBoxLayout()
        vbox_type.addWidget(QLabel("任務類型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["COUNTING", "TIMING"])
        self.type_combo.currentTextChanged.connect(self.toggle_type_fields)
        vbox_type.addWidget(self.type_combo)
        type_layout.addLayout(vbox_type)

        # 任務頻率
        vbox_freq = QVBoxLayout()
        vbox_freq.addWidget(QLabel("頻率:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["ONCE", "PERIODIC"])
        vbox_freq.addWidget(self.freq_combo)
        type_layout.addLayout(vbox_freq)

        layout.addLayout(type_layout)

        # 3. 動態欄位：計數型 vs 計時型
        # 計數型欄位
        self.count_widget = QLabel("目標次數:")
        self.target_count_input = QSpinBox()
        self.target_count_input.setRange(1, 9999)
        
        # 計時型欄位
        self.time_widget = QLabel("目標時間 (HH:MM:SS):")
        self.target_time_input = QTimeEdit()
        self.target_time_input.setDisplayFormat("HH:mm:ss")
        self.target_time_input.setHidden(True)
        self.time_widget.setHidden(True)

        layout.addWidget(self.count_widget)
        layout.addWidget(self.target_count_input)
        layout.addWidget(self.time_widget)
        layout.addWidget(self.target_time_input)

        # 4. 按鈕
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("發布任務")
        self.save_btn.clicked.connect(self.accept) # 關閉視窗並回傳 QDialog.Accepted
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_type_fields(self, task_type):
        """根據選擇的類型顯示/隱藏對應欄位"""
        is_counting = (task_type == "COUNTING")
        self.count_widget.setVisible(is_counting)
        self.target_count_input.setVisible(is_counting)
        self.time_widget.setVisible(not is_counting)
        self.target_time_input.setVisible(not is_counting)

    def get_data(self):
        """將輸入的資料打包成字典回傳"""
        qtime = self.target_time_input.time()
        total_seconds = qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()
        
        return {
            'title': self.title_input.text(),
            'content': self.content_input.text(),
            'description': self.desc_input.toPlainText(),
            'publisher': 'Me', # 這裡可以之後擴充使用者系統
            'task_type': self.type_combo.currentText(),
            'frequency': self.freq_combo.currentText(),
            'target_count': self.target_count_input.value(),
            'total_seconds': total_seconds
        }