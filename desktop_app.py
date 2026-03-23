import sys

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from buddy_session import BuddySession


class ChatWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, session: BuddySession, message: str):
        super().__init__()
        self.session = session
        self.message = message

    def run(self):
        try:
            reply = self.session.reply(self.message)
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(reply)


class BuddyDesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = BuddySession()
        self.worker_thread = None
        self.worker = None

        self.setWindowTitle("Buddy Desktop")
        self.resize(980, 760)
        self._build_ui()
        self._append_buddy_message("你好，我是 Buddy。你可以直接输入问题开始聊天。")

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff6e8,
                    stop:1 #ffe2bf
                );
                border: 1px solid #ead6bb;
                border-radius: 24px;
            }
            """
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(8)

        badge = QLabel("Buddy Desktop · 儿童学习伙伴")
        badge.setStyleSheet(
            """
            QLabel {
                color: #6b7280;
                background: rgba(255,255,255,0.75);
                border: 1px solid #f1c38b;
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 13px;
            }
            """
        )

        title = QLabel("在桌面上和 Buddy 聊天")
        title.setStyleSheet("font-size: 34px; font-weight: 700; color: #1f2937;")

        subtitle = QLabel("先用文字模式跑通桌面版，后面再继续接语音、家长设置和学习面板。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 15px; color: #5f6b76;")

        hero_layout.addWidget(badge, alignment=Qt.AlignLeft)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        body = QHBoxLayout()
        body.setSpacing(16)
        layout.addLayout(body, stretch=1)

        chat_panel = QFrame()
        chat_panel.setStyleSheet(
            """
            QFrame {
                background: #fffaf2;
                border: 1px solid #eadfce;
                border-radius: 24px;
            }
            """
        )
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(18, 18, 18, 18)
        chat_layout.setSpacing(12)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet(
            """
            QTextEdit {
                background: #fffdf9;
                border: 1px solid #eadfce;
                border-radius: 18px;
                padding: 8px;
                font-size: 15px;
            }
            """
        )

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入问题，比如：你是谁、现在几点、帮我讲讲重力")
        self.input_box.setFixedHeight(120)
        self.input_box.setStyleSheet(
            """
            QTextEdit {
                background: white;
                border: 1px solid #eadfce;
                border-radius: 18px;
                padding: 10px;
                font-size: 15px;
            }
            """
        )

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background: #ff7a1a;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:disabled {
                background: #f0b37d;
            }
            """
        )
        self.send_button.clicked.connect(self._send_message)

        self.reset_button = QPushButton("新对话")
        self.reset_button.setStyleSheet(
            """
            QPushButton {
                background: white;
                color: #1f2937;
                border: 1px solid #eadfce;
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 15px;
            }
            """
        )
        self.reset_button.clicked.connect(self._reset_chat)

        self.status_label = QLabel("准备好了")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 14px;")

        controls.addWidget(self.send_button)
        controls.addWidget(self.reset_button)
        controls.addWidget(self.status_label)
        controls.addStretch(1)

        chat_layout.addWidget(self.chat_view, stretch=1)
        chat_layout.addWidget(self.input_box)
        chat_layout.addLayout(controls)

        side_panel = QFrame()
        side_panel.setStyleSheet(
            """
            QFrame {
                background: #fff7ec;
                border: 1px solid #eadfce;
                border-radius: 24px;
            }
            """
        )
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(14)

        side_title = QLabel("快速开始")
        side_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1f2937;")

        side_layout.addWidget(side_title)
        for label, prompt in [
            ("你是谁", "你是谁"),
            ("现在几点", "现在几点"),
            ("讲讲重力", "帮我用小朋友能懂的方式讲什么是重力"),
            ("学习计划", "给8岁小朋友做一个10分钟分数学习计划"),
        ]:
            button = QPushButton(label)
            button.setStyleSheet(
                """
                QPushButton {
                    background: white;
                    color: #1f2937;
                    border: 1px solid #eadfce;
                    border-radius: 16px;
                    padding: 10px 14px;
                    text-align: left;
                    font-size: 14px;
                }
                """
            )
            button.clicked.connect(lambda _checked=False, text=prompt: self.input_box.setPlainText(text))
            side_layout.addWidget(button)

        note = QLabel("当前桌面版是文字聊天入口，后面可以继续接语音输入、TTS 和家长配置。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #6b7280; font-size: 14px; line-height: 1.6;")
        side_layout.addStretch(1)
        side_layout.addWidget(note)

        body.addWidget(chat_panel, stretch=3)
        body.addWidget(side_panel, stretch=1)

    def _append_message(self, speaker: str, text: str, bubble_color: str):
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        html = f"""
        <div style="margin: 10px 0;">
          <div style="
              display: inline-block;
              max-width: 85%;
              padding: 12px 14px;
              border-radius: 18px;
              background: {bubble_color};
              border: 1px solid #eadfce;
              color: #1f2937;
              line-height: 1.6;
          ">
            <div style="font-size: 12px; color: #6b7280; margin-bottom: 6px;">{speaker}</div>
            <div>{safe_text}</div>
          </div>
        </div>
        """
        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.insertHtml(html)
        self.chat_view.moveCursor(QTextCursor.End)

    def _append_user_message(self, text: str):
        self._append_message("You", text, "#ffe3c4")

    def _append_buddy_message(self, text: str):
        self._append_message("Buddy", text, "#ffffff")

    def _send_message(self):
        message = self.input_box.toPlainText().strip()
        if not message:
            return

        self._append_user_message(message)
        self.input_box.clear()
        self.input_box.setFocus()
        self.send_button.setEnabled(False)
        self.status_label.setText("Buddy 正在思考…")

        self.worker_thread = QThread()
        self.worker = ChatWorker(self.session, message)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handle_reply)
        self.worker.failed.connect(self._handle_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _handle_reply(self, reply: str):
        self._append_buddy_message(reply)
        self.send_button.setEnabled(True)
        self.status_label.setText("已完成")

    def _handle_error(self, error_message: str):
        self.send_button.setEnabled(True)
        self.status_label.setText("请求失败")
        QMessageBox.critical(self, "Buddy Error", error_message)

    def _reset_chat(self):
        self.session = BuddySession()
        self.chat_view.clear()
        self._append_buddy_message("新对话已经开始。告诉我你想学什么。")
        self.status_label.setText("已重置")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Buddy Desktop")
    window = BuddyDesktopWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
