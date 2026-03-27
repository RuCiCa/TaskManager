import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QScrollArea, QPushButton, QLabel)

from core.manager import TaskManager
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog


def load_stylesheet(file_path):
    """讀取 QSS 檔案內容"""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = TaskManager()
        self.setWindowTitle("遊戲化任務系統 v1.0")
        self.resize(500, 700)
        
        self.init_ui()
        # 套用外部樣式表
        style_path = os.path.join("resources", "styles", "style.qss")
        self.setStyleSheet(load_stylesheet(style_path))

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 頁籤 1: 目前任務
        self.task_list_tab = QWidget()
        self.task_list_layout = QVBoxLayout()
        
        # 滾動區域 (任務多時可以捲動)
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
        self.stats_tab = QWidget()
        self.stats_layout = QVBoxLayout()
        self.stats_label = QLabel("統計數據載入中...")
        self.stats_layout.addWidget(self.stats_label)
        self.stats_tab.setLayout(self.stats_layout)

        self.tabs.addTab(self.task_list_tab, "目前任務")
        self.tabs.addTab(self.stats_tab, "歷史紀錄與統計")

        self.refresh_tasks()

        self.btn_add_task = QPushButton("＋ 發布新任務")
        self.btn_add_task.clicked.connect(self.show_add_task_dialog)
        self.task_list_layout.insertWidget(0, self.btn_add_task) # 放在最上面

    def refresh_tasks(self):
        """清除舊卡片並重新讀取"""
        # 1. 清除舊 UI
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # 2. 從 Manager 拿資料
        tasks = self.manager.get_all_tasks(status_filter=['PUBLISHED', 'ACCEPTED'])
        
        # 3. 建立新卡片
        for t in tasks:
            card = TaskCard(t, self.manager)
            self.scroll_layout.addWidget(card)
        
        self.scroll_layout.addStretch() # 讓卡片靠上對齊
        self.update_stats()

    def update_stats(self):
        stats = self.manager.get_statistics()
        text = f"""
        <h2>任務統計</h2>
        <p>總發布次數: {stats['total']}</p>
        <p>已完成: {stats['completed']}</p>
        <p>已失敗: {stats['failed']}</p>
        <p>完成率: {stats['completion_rate']:.1f}%</p>
        """
        self.stats_label.setText(text)

    def show_add_task_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec(): # 如果使用者點擊「發布」
            task_data = dialog.get_data()
            self.manager.publish_new_task(task_data)
            self.refresh_tasks() # 重新整理列表

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())