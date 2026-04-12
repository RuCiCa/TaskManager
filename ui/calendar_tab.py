from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QCalendarWidget, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor


# 狀態 → 日曆高亮顏色
_STATUS_COLORS = {
    'PUBLISHED': '#cba6f7',
    'ACCEPTED':  '#89dceb',
    'COMPLETED': '#a6e3a1',
    'FAILED':    '#f38ba8',
}

_STATUS_ICONS = {
    'PUBLISHED': '🟡', 'ACCEPTED': '🔵', 'COMPLETED': '✅', 'FAILED': '❌'
}

_DIFF_TAGS = {'EASY': '[簡]', 'MEDIUM': '[中]', 'HARD': '[難]'}


class CalendarTab(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._highlighted: set[QDate] = set()
        self._all_tasks = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 日曆元件
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        layout.addWidget(self.calendar)

        # 選定日期標題
        self.date_label = QLabel("點選日期查看當日任務")
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        # 當日任務面板
        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_panel = QWidget()
        self.task_panel_layout = QVBoxLayout(self.task_panel)
        self.task_panel_layout.setSpacing(4)
        self.task_panel_layout.setContentsMargins(4, 4, 4, 4)
        self.task_scroll.setWidget(self.task_panel)
        self.task_scroll.setMaximumHeight(180)
        layout.addWidget(self.task_scroll)

    def refresh(self):
        # 清除舊高亮
        empty_fmt = QTextCharFormat()
        for qdate in self._highlighted:
            self.calendar.setDateTextFormat(qdate, empty_fmt)
        self._highlighted.clear()

        # 取得所有任務
        self._all_tasks = self.manager.get_all_tasks()

        # 依截止日期上色
        for task in self._all_tasks:
            deadline_str = getattr(task, 'deadline', None)
            if not deadline_str:
                continue
            qdate = self._parse_date(deadline_str)
            if not qdate:
                continue

            color = _STATUS_COLORS.get(task.status, '#cba6f7')
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(color))
            fmt.setForeground(QColor('#11111b'))
            self.calendar.setDateTextFormat(qdate, fmt)
            self._highlighted.add(qdate)

        self._on_date_selected()

    def _parse_date(self, deadline_str: str):
        try:
            date_part = deadline_str.split(' ')[0]
            y, m, d = date_part.split('-')
            return QDate(int(y), int(m), int(d))
        except (ValueError, AttributeError):
            return None

    def _on_date_selected(self):
        selected = self.calendar.selectedDate()
        date_str = selected.toString("yyyy-MM-dd")
        self.date_label.setText(f"📅  {date_str} 的截止任務")

        # 清空面板
        while self.task_panel_layout.count():
            item = self.task_panel_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        day_tasks = [t for t in self._all_tasks
                     if getattr(t, 'deadline', None) and t.deadline.startswith(date_str)]

        if not day_tasks:
            empty = QLabel("這天沒有截止任務")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #585b70; padding: 8px;")
            self.task_panel_layout.addWidget(empty)
        else:
            for task in day_tasks:
                icon = _STATUS_ICONS.get(task.status, '⚪')
                diff = _DIFF_TAGS.get(getattr(task, 'difficulty', 'MEDIUM'), '[中]')
                entry = QLabel(f"  {icon} {diff} {task.title}")
                entry.setStyleSheet(
                    "background-color: #313244; padding: 5px 8px;"
                    "border-radius: 6px; margin: 1px 0;"
                )
                self.task_panel_layout.addWidget(entry)

        self.task_panel_layout.addStretch()
