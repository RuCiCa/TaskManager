import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton,
                             QLabel, QProgressBar, QSystemTrayIcon, QMenu,
                             QMessageBox)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon

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

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.window_width = 500
        self.window_height = 750
        self.resize(self.window_width, self.window_height)

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
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        self.peek_width = 20
        y_pos = (screen_height - self.window_height) // 2
        self.expanded_pos = QPoint(screen_width - self.window_width, y_pos)
        self.collapsed_pos = QPoint(screen_width - self.peek_width, y_pos)

        self.move(self.collapsed_pos)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setEndValue(self.expanded_pos)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setEndValue(self.collapsed_pos)
        self.animation.start()
        super().leaveEvent(event)

    # ── 系統列圖示 ─────────────────────────────────────────────

    def setup_tray(self):
        # 使用 Qt 內建圖示，無需外部圖片
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("遊戲化任務系統")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("顯示視窗")
        show_action.triggered.connect(self.show_window)
        quit_action = tray_menu.addAction("離開")
        quit_action.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda reason: self.show_window()
                                    if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """關閉按鈕改為縮小到系統列"""
        event.ignore()
        self.hide()
        self.tray.showMessage("遊戲化任務系統", "程式已縮小到系統列，雙擊圖示可重新開啟。",
                              QSystemTrayIcon.MessageIcon.Information, 2000)

    # ── UI 初始化 ──────────────────────────────────────────────

    def init_ui(self):
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainContainer")
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 頂部工具列
        top_bar = QHBoxLayout()
        self.title_label = QLabel(" 🎮 遊戲化任務系統")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")

        btn_close = QPushButton("✖")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; border-radius: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        btn_close.clicked.connect(self.close)

        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(btn_close)
        self.main_layout.addLayout(top_bar)

        # EXP / 等級列
        exp_bar_row = QHBoxLayout()
        self.level_label = QLabel("Lv.1")
        self.level_label.setObjectName("LevelLabel")
        self.level_label.setMinimumWidth(42)

        self.exp_bar = QProgressBar()
        self.exp_bar.setObjectName("ExpBar")
        self.exp_bar.setTextVisible(True)
        self.exp_bar.setFormat("%v / %m EXP")
        self.exp_bar.setFixedHeight(18)

        exp_bar_row.addWidget(self.level_label)
        exp_bar_row.addWidget(self.exp_bar)
        self.main_layout.addLayout(exp_bar_row)

        # 分頁
        self.tabs = QTabWidget()

        # 任務列表頁
        task_list_tab = QWidget()
        task_list_layout = QVBoxLayout()

        btn_add_task = QPushButton("＋ 發布新任務")
        btn_add_task.clicked.connect(self.show_add_task_dialog)
        task_list_layout.addWidget(btn_add_task)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        task_list_layout.addWidget(scroll)

        btn_refresh = QPushButton("重新整理")
        btn_refresh.clicked.connect(self.refresh_tasks)
        task_list_layout.addWidget(btn_refresh)

        task_list_tab.setLayout(task_list_layout)

        self.history_tab = HistoryTab(self.manager)

        self.tabs.addTab(task_list_tab, "目前任務")
        self.tabs.addTab(self.history_tab, "歷史紀錄")

        self.main_layout.addWidget(self.tabs)
        self.setCentralWidget(self.main_widget)

    # ── EXP 條更新 ─────────────────────────────────────────────

    def update_exp_bar(self):
        profile = self.manager.get_profile()
        level = profile['level']
        current_exp = profile['current_exp']
        threshold = level * 100
        self.level_label.setText(f"Lv.{level}")
        self.exp_bar.setMaximum(threshold)
        self.exp_bar.setValue(current_exp)

    # ── 任務清單 ───────────────────────────────────────────────

    def refresh_tasks(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for t in self.manager.get_all_tasks(status_filter=['PUBLISHED', 'ACCEPTED']):
            self.scroll_layout.addWidget(TaskCard(t, self.manager))

        self.scroll_layout.addStretch()

        if hasattr(self, 'history_tab'):
            self.history_tab.refresh()

    def _handle_complete_result(self, result, task_title=""):
        """處理完成任務後的 EXP 更新與通知"""
        if not result:
            return
        self.update_exp_bar()

        if result.get('leveled_up'):
            new_level = result['new_level']
            self.tray.showMessage("🎉 升級了！", f"恭喜達到 Lv.{new_level}！繼續保持！",
                                  QSystemTrayIcon.MessageIcon.Information, 3000)

        for ach in result.get('new_achievements', []):
            self.tray.showMessage(f"🏅 成就解鎖：{ach['name']}", ach['description'],
                                  QSystemTrayIcon.MessageIcon.Information, 3000)
            if hasattr(self, 'history_tab'):
                self.history_tab.refresh()

    # ── 計時器 ─────────────────────────────────────────────────

    def on_timer_tick(self):
        # 截止時間檢查
        failed_ids = self.manager.check_deadlines()
        if failed_ids:
            self.refresh_tasks()
            for fid in failed_ids:
                self.tray.showMessage("任務逾期", f"有 {len(failed_ids)} 個任務已超過截止時間，標記為失敗。",
                                      QSystemTrayIcon.MessageIcon.Warning, 3000)
            return  # refresh_tasks 已處理完畢

        # 計時型任務倒數
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
                    self.tray.showMessage("計時完成！", f"任務「{card.task.title}」已完成！",
                                          QSystemTrayIcon.MessageIcon.Information, 3000)
                    self._handle_complete_result(result, card.task.title)
                    needs_refresh = True

        if needs_refresh:
            self.refresh_tasks()

    # ── 新增任務 ───────────────────────────────────────────────

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
