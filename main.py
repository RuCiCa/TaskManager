import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QLabel)
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QMouseEvent

from core.manager import TaskManager
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog
from ui.history_tab import HistoryTab

def load_stylesheet(file_name):
    """使用絕對路徑確保能讀取到 QSS"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "resources", "styles", file_name)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"警告：找不到樣式表檔案！")
        return ""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = TaskManager()
        self.resize(500, 700)
        
        # --- 無邊框視窗設定 ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # 讓背景支援透明圓角
        self.drag_pos = None # 用於紀錄滑鼠拖曳位置
        
        # 1. 初始化 UI
        self.init_ui()
        
        # 2. 設定計時器 (每 1 秒執行一次)
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(1000)
        
        # 3. 初始刷新
        self.refresh_tasks()

    def init_ui(self):
        # 建立一個主容器來包裝「自訂標題列」和「原本的頁籤」
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainContainer") # 給 QSS 抓取用
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # 留邊距才看得出圓角
        
        # --- 自訂頂部標題列 ---
        self.top_bar = QHBoxLayout()
        
        self.title_label = QLabel(" 🎮 遊戲化任務系統 v1.0")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        
        self.btn_close = QPushButton("✖")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; border-radius: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.btn_close.clicked.connect(self.close) # 點擊後關閉程式
        
        self.top_bar.addWidget(self.title_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.btn_close)
        
        self.main_layout.addLayout(self.top_bar)
        # ---------------------

        # --- 原本的頁籤內容 ---
        self.tabs = QTabWidget()
        
        # 頁籤 1: 目前任務
        self.task_list_tab = QWidget()
        self.task_list_layout = QVBoxLayout()
        
        self.btn_add_task = QPushButton("＋ 發布新任務")
        self.btn_add_task.clicked.connect(self.show_add_task_dialog)
        self.task_list_layout.addWidget(self.btn_add_task)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        self.task_list_layout.addWidget(scroll)
        
        btn_refresh = QPushButton("重新整理任務列表")
        btn_refresh.clicked.connect(self.refresh_tasks)
        self.task_list_layout.addWidget(btn_refresh)
        
        self.task_list_tab.setLayout(self.task_list_layout)

        # 頁籤 2: 歷史紀錄與統計
        self.history_tab = HistoryTab(self.manager)

        self.tabs.addTab(self.task_list_tab, "目前任務")
        self.tabs.addTab(self.history_tab, "歷史紀錄與統計")

        self.main_layout.addWidget(self.tabs)
        
        # 將包好的主容器設定為 CentralWidget
        self.setCentralWidget(self.main_widget)

    # --- 滑鼠拖曳視窗邏輯 ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if hasattr(self, 'drag_pos') and self.drag_pos is not None:
            # 計算滑鼠移動的距離
            delta = event.globalPosition().toPoint() - self.drag_pos
            # 移動整個視窗
            self.move(self.pos() + delta)
            # 更新滑鼠位置
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None
        event.accept()
    # ----------------------

    def refresh_tasks(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        tasks = self.manager.get_all_tasks(status_filter=['PUBLISHED', 'ACCEPTED'])
        
        for t in tasks:
            card = TaskCard(t, self.manager)
            self.scroll_layout.addWidget(card)
        
        self.scroll_layout.addStretch() 
        
        if hasattr(self, 'history_tab'):
            self.history_tab.refresh()

    def on_timer_tick(self):
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                if isinstance(card, TaskCard) and card.task.status == 'ACCEPTED':
                    if hasattr(card.task, 'tick'): 
                        if card.task.tick(1): 
                            self.manager.update_timing_task(card.task.id, card.task.remaining_seconds)
                            card.update_ui_display()
                            
                            if card.task.status == 'COMPLETED':
                                self.refresh_tasks()

    def show_add_task_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec():
            task_data = dialog.get_data()
            self.manager.publish_new_task(task_data)
            self.refresh_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    full_style = load_stylesheet("style.qss")
    app.setStyleSheet(full_style)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())