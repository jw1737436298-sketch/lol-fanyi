from __future__ import annotations

import sys
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable

import pyperclip
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .config import AppConfig, ensure_user_config_exists, load_config
from .hotkeys import HotkeyManager
from .translator import TranslationError, create_translator


class OverlayWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.hotkeys = HotkeyManager()
        self.translator = None

        self.setWindowTitle("LOL 双向翻译悬浮窗")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        self.resize(460, 420)

        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("粘贴英文/德文聊天，或输入中文...")
        self.result_edit = QPlainTextEdit()
        self.result_edit.setPlaceholderText("翻译结果会显示在这里")
        self.result_edit.setReadOnly(True)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.to_chinese_button = QPushButton("译成中文")
        self.to_english_button = QPushButton("中文译成英文并复制")
        self.clipboard_button = QPushButton("翻译剪贴板")
        self.copy_button = QPushButton("复制结果")
        self.auto_copy_checkbox = QCheckBox("翻译成英文后直接复制")
        self.auto_copy_checkbox.setChecked(self.config.auto_copy_english)

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.to_chinese_button)
        top_buttons.addWidget(self.to_english_button)

        bottom_buttons = QHBoxLayout()
        bottom_buttons.addWidget(self.clipboard_button)
        bottom_buttons.addWidget(self.copy_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("输入"))
        layout.addWidget(self.source_edit)
        layout.addWidget(self.auto_copy_checkbox)
        layout.addLayout(top_buttons)
        layout.addWidget(QLabel("结果"))
        layout.addWidget(self.result_edit)
        layout.addLayout(bottom_buttons)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.to_chinese_button.clicked.connect(self.translate_input_to_chinese)
        self.to_english_button.clicked.connect(self.translate_input_to_english)
        self.clipboard_button.clicked.connect(self.translate_clipboard_to_chinese)
        self.copy_button.clicked.connect(self.copy_result)

        self.tray = self._create_tray()
        self._initialize_translator()
        self._register_hotkeys()

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(self)
        tray.setToolTip("LOL 双向翻译悬浮窗")

        menu = QMenu()
        show_action = QAction("显示/隐藏", self)
        quit_action = QAction("退出", self)
        show_action.triggered.connect(self.toggle_visible)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.show()
        return tray

    def _initialize_translator(self) -> None:
        try:
            self.translator = create_translator(self.config)
            self.status.showMessage("翻译服务已就绪")
        except TranslationError as exc:
            self.status.showMessage(str(exc))
            QMessageBox.warning(self, "配置需要补充", str(exc))

    def _register_hotkeys(self) -> None:
        try:
            self.hotkeys.register(self.config.hotkey_toggle, self._post_to_ui(self.toggle_visible))
            self.hotkeys.register(
                self.config.hotkey_clipboard_to_chinese,
                self._post_to_ui(self.translate_clipboard_to_chinese),
            )
            self.hotkeys.register(
                self.config.hotkey_chinese_to_english,
                self._post_to_ui(self.translate_input_to_english),
            )
            self.status.showMessage(
                f"快捷键：{self.config.hotkey_toggle} 呼出/隐藏，"
                f"{self.config.hotkey_clipboard_to_chinese} 翻译剪贴板，"
                f"{self.config.hotkey_chinese_to_english} 中文转英文"
            )
        except Exception as exc:
            self.status.showMessage(f"快捷键注册失败：{exc}")

    def _post_to_ui(self, func: Callable[[], None]) -> Callable[[], None]:
        def wrapper() -> None:
            QTimer.singleShot(0, func)

        return wrapper

    def _run_translation(self, job: Callable[[], str], copy_after: bool = False) -> None:
        if self.translator is None:
            self._initialize_translator()
            if self.translator is None:
                return

        self._set_busy(True)
        future = self.executor.submit(job)
        future.add_done_callback(lambda done: QTimer.singleShot(0, lambda: self._finish_translation(done, copy_after)))

    def _finish_translation(self, future: Future[str], copy_after: bool) -> None:
        self._set_busy(False)
        try:
            result = future.result()
        except Exception as exc:
            self.status.showMessage(f"翻译失败：{exc}")
            return

        self.result_edit.setPlainText(result)
        if copy_after and result:
            pyperclip.copy(result)
            self.status.showMessage("已翻译并复制到剪贴板，可以切回 LOL 粘贴发送")
        else:
            self.status.showMessage("翻译完成")

    def _set_busy(self, busy: bool) -> None:
        for button in [self.to_chinese_button, self.to_english_button, self.clipboard_button, self.copy_button]:
            button.setEnabled(not busy)
        if busy:
            self.status.showMessage("正在翻译...")

    def translate_input_to_chinese(self) -> None:
        text = self.source_edit.toPlainText()
        self._run_translation(lambda: self.translator.to_chinese(text))

    def translate_clipboard_to_chinese(self) -> None:
        text = pyperclip.paste()
        self.source_edit.setPlainText(text)
        self.show()
        self.raise_()
        self.activateWindow()
        self._run_translation(lambda: self.translator.to_chinese(text), copy_after=self.config.auto_copy_clipboard_translation)

    def translate_input_to_english(self) -> None:
        text = self.source_edit.toPlainText()
        self.show()
        self.raise_()
        self.activateWindow()
        self._run_translation(
            lambda: self.translator.chinese_to_game_english(text),
            copy_after=self.auto_copy_checkbox.isChecked(),
        )

    def copy_result(self) -> None:
        result = self.result_edit.toPlainText().strip()
        if result:
            pyperclip.copy(result)
            self.status.showMessage("结果已复制")

    def toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
        self.status.showMessage("已隐藏到托盘")

    def shutdown(self) -> None:
        self.hotkeys.unregister_all()
        self.executor.shutdown(wait=False, cancel_futures=True)


def main() -> int:
    ensure_user_config_exists()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = OverlayWindow(load_config())
    app.aboutToQuit.connect(window.shutdown)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
