import csv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QHeaderView, QHBoxLayout,
                             QPushButton, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class HistoryTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. 統計摘要
        self.stats_summary = QLabel("載入統計中...")
        self.stats_summary.setObjectName("StatsSummary")
        layout.addWidget(self.stats_summary)

        # 2. 成就徽章區
        ach_header = QLabel("🏅 成就徽章")
        ach_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #f9e2af; margin-top: 6px;")
        layout.addWidget(ach_header)

        self.achievement_scroll = QScrollArea()
        self.achievement_scroll.setWidgetResizable(True)
        self.achievement_scroll.setFixedHeight(72)
        self.achievement_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.achievement_content = QWidget()
        self.achievement_layout = QHBoxLayout(self.achievement_content)
        self.achievement_layout.setContentsMargins(4, 4, 4, 4)
        self.achievement_scroll.setWidget(self.achievement_content)
        layout.addWidget(self.achievement_scroll)

        # 3. 歷史紀錄標題列 + 匯出按鈕
        history_row = QHBoxLayout()
        history_label = QLabel("📜 歷史紀錄")
        history_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #89b4fa;")
        self.export_btn = QPushButton("匯出 CSV")
        self.export_btn.setFixedWidth(90)
        self.export_btn.clicked.connect(self.export_csv)
        history_row.addWidget(history_label)
        history_row.addStretch()
        history_row.addWidget(self.export_btn)
        layout.addLayout(history_row)

        # 4. 歷史表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["任務名稱", "類型", "難度", "狀態", "完成時間", "發布人"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def refresh(self):
        # 統計
        stats = self.manager.get_statistics()
        self.stats_summary.setText(
            f"總結：共發布 {stats['total']} 個任務 | "
            f"已完成 {stats['completed']} | "
            f"已失敗 {stats['failed']} | "
            f"完成率 {stats['completion_rate']:.1f}%"
        )

        self._refresh_achievements()

        # 表格
        history_tasks = self.manager.get_history_tasks()
        self.table.setRowCount(len(history_tasks))

        diff_colors = {'EASY': '#a6e3a1', 'MEDIUM': '#f9e2af', 'HARD': '#f38ba8'}

        for row, task in enumerate(history_tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task.title or ''))
            self.table.setItem(row, 1, QTableWidgetItem(getattr(task, 'task_type', '') or ''))

            diff = getattr(task, 'difficulty', 'MEDIUM') or 'MEDIUM'
            diff_item = QTableWidgetItem(diff)
            diff_item.setForeground(QColor(diff_colors.get(diff, '#cdd6f4')))
            self.table.setItem(row, 2, diff_item)

            status_item = QTableWidgetItem(task.status)
            status_item.setForeground(QColor('#a6e3a1' if task.status == 'COMPLETED' else '#f38ba8'))
            self.table.setItem(row, 3, status_item)

            finish_time = getattr(task, 'completed_at', '---') or '---'
            self.table.setItem(row, 4, QTableWidgetItem(str(finish_time)))
            self.table.setItem(row, 5, QTableWidgetItem(task.publisher or ''))

    def _refresh_achievements(self):
        while self.achievement_layout.count():
            item = self.achievement_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for ach in self.manager.get_all_achievements():
            unlocked = bool(ach['unlocked_at'])
            badge = QLabel(f"{'🏅' if unlocked else '🔒'} {ach['name']}")
            badge.setToolTip(ach['description'])
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if unlocked:
                badge.setStyleSheet(
                    "background-color: #313244; color: #f9e2af;"
                    "border: 1px solid #f9e2af; border-radius: 8px; padding: 4px 8px; font-size: 11px;")
            else:
                badge.setStyleSheet(
                    "background-color: #1e1e2e; color: #585b70;"
                    "border: 1px solid #45475a; border-radius: 8px; padding: 4px 8px; font-size: 11px;")
            self.achievement_layout.addWidget(badge)

        self.achievement_layout.addStretch()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "匯出歷史紀錄", "task_history.csv", "CSV 檔案 (*.csv)"
        )
        if not path:
            return

        history_tasks = self.manager.get_history_tasks()
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['任務名稱', '類型', '難度', '狀態', '完成時間', '發布人'])
            for task in history_tasks:
                writer.writerow([
                    task.title or '',
                    getattr(task, 'task_type', '') or '',
                    getattr(task, 'difficulty', 'MEDIUM') or 'MEDIUM',
                    task.status,
                    getattr(task, 'completed_at', '') or '',
                    task.publisher or '',
                ])
