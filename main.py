import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QScrollArea, QPushButton, QLabel)
from PyQt6.QtCore import QTimer

from core.manager import TaskManager
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog
from ui.history_tab import HistoryTab


def load_stylesheet(file_name):
    """使用絕對路徑確保能讀取到 QSS"""
    # 取得 main.py 的絕對路徑
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 組合出 resources/styles/style.qss 的路徑
    file_path = os.path.join(base_dir, "resources", "styles", file_name)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            print(f"成功載入樣式表: {file_path}") # 除錯用
            return f.read()
    else:
        print(f"警告：找不到樣式表檔案！路徑應為: {file_path}")
        return ""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = TaskManager()
        self.setWindowTitle("遊戲化任務系統 v1.0")
        self.resize(500, 700)
        
        # 初始化 UI
        self.init_ui()

        # 設定計時器 (每 1 秒執行一次)
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(1000)

        self.refresh_tasks()

        # 套用外部樣式表
        style_content = load_stylesheet("style.qss")
        if style_content:
            self.setStyleSheet(style_content)

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 頁籤 1: 目前任務
        self.task_list_tab = QWidget()
        self.task_list_layout = QVBoxLayout()

        self.btn_add_task = QPushButton("＋ 發布新任務")
        self.btn_add_task.clicked.connect(self.show_add_task_dialog)
        self.task_list_layout.insertWidget(0, self.btn_add_task) # 放在最上面

        # 滾動區域 
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

        # 頁籤 2: 統計報表
        self.history_tab = HistoryTab(self.manager)

        self.tabs.addTab(self.task_list_tab, "目前任務")
        self.tabs.addTab(self.stats_tab, "歷史紀錄與統計")

        self.refresh_tasks()


    def refresh_tasks(self):
        """清除舊卡片並重新讀取"""
        # 清除舊 UI
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # 從 Manager 拿資料
        tasks = self.manager.get_all_tasks(status_filter=['PUBLISHED', 'ACCEPTED'])
        
        # 建立新卡片
        for t in tasks:
            card = TaskCard(t, self.manager)
            self.scroll_layout.addWidget(card)
        
        self.scroll_layout.addStretch() 
        # 同步刷新歷史頁籤
        if hasattr(self, 'history_tab'):
            self.history_tab.refresh()

    def on_timer_tick(self):
        """每秒鐘觸發一次，檢查並更新計時任務"""
        # 遍歷 scroll_layout 裡所有的 TaskCard
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                # 如果卡片是 TaskCard 且 任務正在進行中 (ACCEPTED) 且 是計時型
                if isinstance(card, TaskCard) and card.task.status == 'ACCEPTED':
                    if hasattr(card.task, 'tick'): # 檢查是否有 tick 方法 (計時型任務才有)
                        if card.task.tick(1): # 減少 1 秒
                            # 更新資料庫
                            self.manager.update_timing_task(card.task.id, card.task.remaining_seconds)
                            # 更新卡片顯示
                            card.update_ui_display()
                            
                            # 如果時間到完成了，刷新列表
                            if card.task.status == 'COMPLETED':
                                self.refresh_tasks()

    def show_add_task_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec(): # 如果使用者點擊「發布」
            task_data = dialog.get_data()
            self.manager.publish_new_task(task_data)
            self.refresh_tasks() # 重新整理列表

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    full_style = load_stylesheet("style.qss")
    app.setStyleSheet(full_style)

    window.show()
    sys.exit(app.exec())