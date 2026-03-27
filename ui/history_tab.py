from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QHBoxLayout)
from PyQt6.QtCore import Qt

class HistoryTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. 頂部統計數據區
        self.stats_summary = QLabel("載入統計中...")
        self.stats_summary.setObjectName("StatsSummary") # 方便 QSS 定義樣式
        layout.addWidget(self.stats_summary)

        # 2. 歷史紀錄表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["任務名稱", "類型", "狀態", "完成時間", "發布人"])
        
        # 讓表格欄位自動伸展
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def refresh(self):
        """刷新歷史紀錄與統計"""
        # 更新統計文字
        stats = self.manager.get_statistics()
        self.stats_summary.setText(
            f"總結：共發布 {stats['total']} 個任務 | "
            f"已完成 {stats['completed']} | "
            f"已失敗 {stats['failed']} | "
            f"完成率 {stats['completion_rate']:.1f}%"
        )

        # 更新表格內容
        history_tasks = self.manager.get_history_tasks()
        self.table.setRowCount(len(history_tasks))
        
        for row, task in enumerate(history_tasks):
            # 填入資料
            self.table.setItem(row, 0, QTableWidgetItem(task.title))
            self.table.setItem(row, 1, QTableWidgetItem(getattr(task, 'task_type', 'N/A')))
            
            # 狀態帶有顏色文字
            status_item = QTableWidgetItem(task.status)
            if task.status == 'COMPLETED':
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)
            
            # 取得完成時間 (從原始 dict 取得，或在物件中定義)
            # 假設我們從資料庫字典中讀取
            finish_time = getattr(task, 'completed_at', '---') or '---'
            self.table.setItem(row, 3, QTableWidgetItem(str(finish_time)))
            self.table.setItem(row, 4, QTableWidgetItem(task.publisher))