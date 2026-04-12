import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton,
                             QLabel, QProgressBar, QSystemTrayIcon, QMenu,
                             QFrame)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QPoint

from core.manager import TaskManager
from ui.task_card import TaskCard
from ui.task_dialog import TaskDialog
from ui.history_tab import HistoryTab
from ui.ai_chat_tab import AiChatTab
from ui.calendar_tab import CalendarTab


def load_stylesheet(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "resources", "styles", file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


class DragHandle(QFrame):
    """左側拖動把手 — 負責觸發主視窗的拖曳邏輯"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.setObjectName("DragHandle")
        self.setFixedWidth(14)
        self.setCursor(Qt.CursorShape.SizeHorCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.mw._drag_active = True
            self.mw._drag_offset = (
                e.globalPosition().toPoint() - self.mw.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and self.mw._drag_active:
            self.mw._on_drag_move(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e):
        self.mw._drag_active = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = TaskManager()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.window_width = 500
        self.window_height = 750
        self.resize(self.window_width, self.window_height)

        # 拖動狀態
        self.is_floating = False
        self._drag_active = False
        self._drag_offset = QPoint()

        self.init_ui()
        self.setup_sidebar_animation()
        self.setup_tray()

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(1000)

        self.refresh_tasks()
        self.update_exp_bar()

    # ── 側邊欄動畫 ─────────────────────────────────────────────

    def setup_sidebar_animation(self):
        geo = QApplication.primaryScreen().availableGeometry()
        sw, sh = geo.width(), geo.height()
        self.peek_width = 14  # 只露出拖動把手
        y_pos = (sh - self.window_height) // 2
        self.expanded_pos = QPoint(sw - self.window_width, y_pos)
        self.collapsed_pos = QPoint(sw - self.peek_width, y_pos)
        self.move(self.collapsed_pos)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        if not self.is_floating:
            self.animation.stop()
            self.animation.setEndValue(self.expanded_pos)
            self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_floating:
            self.animation.stop()
            self.animation.setEndValue(self.collapsed_pos)
            self.animation.start()
        super().leaveEvent(event)

    # ── 拖動邏輯 ───────────────────────────────────────────────

    def _on_drag_move(self, global_pos: QPoint):
        if not self.is_floating:
            self.is_floating = True
            self.animation.stop()

        new_pos = global_pos - self._drag_offset
        self.move(new_pos)

        # 靠近右側螢幕邊緣時自動吸附
        sw = QApplication.primaryScreen().availableGeometry().width()
        if sw - (new_pos.x() + self.window_width) <= 50:
            self._snap_to_sidebar()

    def _snap_to_sidebar(self):
        self.is_floating = False
        self._drag_active = False
        self.animation.stop()
        self.animation.setEndValue(self.collapsed_pos)
        self.animation.start()

    # ── 系統列 ─────────────────────────────────────────────────

    def setup_tray(self):
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("遊戲化任務系統")

        menu = QMenu()
        menu.addAction("顯示視窗").triggered.connect(self.show_window)
        menu.addAction("離開").triggered.connect(QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.show_window()
            if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "遊戲化任務系統", "已縮小到系統列，雙擊圖示重新開啟。",
            QSystemTrayIcon.MessageIcon.Information, 2000
        )

    # ── UI 初始化 ──────────────────────────────────────────────

    def init_ui(self):
        # 最外層：透明容器，左側拖動把手 + 右側主內容
        outer = QWidget()
        outer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer_layout = QHBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 拖動把手
        self.drag_handle = DragHandle(self)
        outer_layout.addWidget(self.drag_handle)

        # 主內容區
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainContainer")
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(self.main_widget)

        self.setCentralWidget(outer)

        # 頂部列（無關閉按鈕 — 改由系統列控制）
        top_bar = QHBoxLayout()
        title_label = QLabel(" 🎮 遊戲化任務系統")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa;")
        top_bar.addWidget(title_label)
        top_bar.addStretch()
        self.main_layout.addLayout(top_bar)

        # EXP 列
        exp_row = QHBoxLayout()
        self.level_label = QLabel("Lv.1")
        self.level_label.setObjectName("LevelLabel")
        self.level_label.setMinimumWidth(42)
        self.exp_bar = QProgressBar()
        self.exp_bar.setObjectName("ExpBar")
        self.exp_bar.setTextVisible(True)
        self.exp_bar.setFormat("%v / %m EXP")
        self.exp_bar.setFixedHeight(18)
        exp_row.addWidget(self.level_label)
        exp_row.addWidget(self.exp_bar)
        self.main_layout.addLayout(exp_row)

        # 分頁
        self.tabs = QTabWidget()

        # ── 目前任務 tab
        task_tab = QWidget()
        task_layout = QVBoxLayout()
        btn_add = QPushButton("＋ 發布新任務")
        btn_add.clicked.connect(self.show_add_task_dialog)
        task_layout.addWidget(btn_add)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        task_layout.addWidget(scroll)
        btn_refresh = QPushButton("重新整理")
        btn_refresh.clicked.connect(self.refresh_tasks)
        task_layout.addWidget(btn_refresh)
        task_tab.setLayout(task_layout)

        # ── 歷史紀錄 tab
        self.history_tab = HistoryTab(self.manager)

        # ── AI 聊天 tab
        self.ai_chat_tab = AiChatTab(self.manager)

        # ── 行事曆 tab
        self.calendar_tab = CalendarTab(self.manager)

        self.tabs.addTab(task_tab, "目前任務")
        self.tabs.addTab(self.history_tab, "歷史紀錄")
        self.tabs.addTab(self.ai_chat_tab, "AI 聊天")
        self.tabs.addTab(self.calendar_tab, "行事曆")

        self.main_layout.addWidget(self.tabs)

    # ── EXP 條 ─────────────────────────────────────────────────

    def update_exp_bar(self):
        p = self.manager.get_profile()
        self.level_label.setText(f"Lv.{p['level']}")
        self.exp_bar.setMaximum(p['level'] * 100)
        self.exp_bar.setValue(p['current_exp'])

    # ── 任務清單 ───────────────────────────────────────────────

    def refresh_tasks(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for t in self.manager.get_all_tasks(status_filter=['PUBLISHED', 'ACCEPTED']):
            self.scroll_layout.addWidget(TaskCard(t, self.manager))

        self.scroll_layout.addStretch()

        if hasattr(self, 'history_tab'):
            self.history_tab.refresh()
        if hasattr(self, 'calendar_tab'):
            self.calendar_tab.refresh()

    def _handle_complete_result(self, result, task_title=""):
        if not result:
            return
        self.update_exp_bar()
        if result.get('leveled_up'):
            self.tray.showMessage(
                "🎉 升級了！", f"恭喜達到 Lv.{result['new_level']}！繼續保持！",
                QSystemTrayIcon.MessageIcon.Information, 3000
            )
        for ach in result.get('new_achievements', []):
            self.tray.showMessage(
                f"🏅 成就解鎖：{ach['name']}", ach['description'],
                QSystemTrayIcon.MessageIcon.Information, 3000
            )
        if result.get('new_achievements') and hasattr(self, 'history_tab'):
            self.history_tab.refresh()

    # ── 計時器 ─────────────────────────────────────────────────

    def on_timer_tick(self):
        failed_ids = self.manager.check_deadlines()
        if failed_ids:
            self.tray.showMessage(
                "任務逾期",
                f"有 {len(failed_ids)} 個任務已超過截止時間，標記為失敗。",
                QSystemTrayIcon.MessageIcon.Warning, 3000
            )
            self.refresh_tasks()
            return

        needs_refresh = False
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if not (item and item.widget()):
                continue
            card = item.widget()
            if not isinstance(card, TaskCard) or card.task.status != 'ACCEPTED':
                continue
            if not hasattr(card.task, 'tick'):
                continue
            if card.task.tick(1):
                result = self.manager.update_timing_task(card.task.id, card.task.remaining_seconds)
                card.update_ui_display()
                if card.task.status == 'COMPLETED':
                    self.tray.showMessage(
                        "計時完成！", f"任務「{card.task.title}」已完成！",
                        QSystemTrayIcon.MessageIcon.Information, 3000
                    )
                    self._handle_complete_result(result, card.task.title)
                    needs_refresh = True

        if needs_refresh:
            self.refresh_tasks()

    # ── 新增任務 ───────────────────────────────────────────────

    def show_add_task_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec():
            self.manager.publish_new_task(dialog.get_data())
            self.refresh_tasks()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet("style.qss"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
