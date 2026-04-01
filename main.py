import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QLabel)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QPoint

from core.manager import TaskManager
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog
from ui.history_tab import HistoryTab

def load_stylesheet(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "resources", "styles", file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = TaskManager()
        
        # --- 視窗設定 ---
        # 加入 WindowStaysOnTopHint 讓它像工具列一樣永遠在最上層
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.window_width = 500
        self.window_height = 700
        self.resize(self.window_width, self.window_height)
        
        # 1. 初始化 UI
        self.init_ui()
        
        # 2. 設定側邊欄隱藏邏輯與動畫
        self.setup_sidebar_animation()
        
        # 3. 設定計時器
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(1000)
        
        self.refresh_tasks()

    def setup_sidebar_animation(self):
        """設定螢幕定位與滑動動畫"""
        # 取得主螢幕尺寸
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # 隱藏時，要露出一點點邊緣讓滑鼠可以碰到 (大約 20 pixel)
        self.peek_width = 20 

        # 計算展開與隱藏時的座標 (垂直置中，靠右)
        y_pos = (screen_height - self.window_height) // 2
        self.expanded_pos = QPoint(screen_width - self.window_width, y_pos)
        self.collapsed_pos = QPoint(screen_width - self.peek_width, y_pos)

        # 初始狀態設為隱藏
        self.move(self.collapsed_pos)

        # 建立動畫物件，綁定視窗的 "pos" (位置) 屬性
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250) # 動畫時間 250 毫秒
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic) # 平滑減速特效

    # --- 滑鼠進入與離開事件 ---
    def enterEvent(self, event):
        """當滑鼠碰到視窗邊緣時，展開視窗"""
        self.animation.stop()
        self.animation.setEndValue(self.expanded_pos)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """當滑鼠離開視窗範圍時，收合視窗"""
        self.animation.stop()
        self.animation.setEndValue(self.collapsed_pos)
        self.animation.start()
        super().leaveEvent(event)
    # ------------------------

    def init_ui(self):
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainContainer")
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.top_bar = QHBoxLayout()
        self.title_label = QLabel(" 🎮 遊戲化任務系統")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        
        self.btn_close = QPushButton("✖")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; border-radius: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.btn_close.clicked.connect(self.close)
        
        self.top_bar.addWidget(self.title_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.btn_close)
        
        self.main_layout.addLayout(self.top_bar)

        self.tabs = QTabWidget()
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
        
        btn_refresh = QPushButton("重新整理")
        btn_refresh.clicked.connect(self.refresh_tasks)
        self.task_list_layout.addWidget(btn_refresh)
        
        self.task_list_tab.setLayout(self.task_list_layout)

        self.history_tab = HistoryTab(self.manager)

        self.tabs.addTab(self.task_list_tab, "目前任務")
        self.tabs.addTab(self.history_tab, "歷史紀錄")

        self.main_layout.addWidget(self.tabs)
        self.setCentralWidget(self.main_widget)

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