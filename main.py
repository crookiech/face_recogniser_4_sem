import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QHBoxLayout,QInputDialog, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QEvent
from PyQt6.QtGui import (QIcon, QFont, QColor, QLinearGradient, QPalette, QPainter, QBrush, QMovie)

class RenameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Переименование пользователя")

        self.oldNameEdit = QLineEdit()
        self.newNameEdit = QLineEdit()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Старое имя:"))
        layout.addWidget(self.oldNameEdit)

        layout.addWidget(QLabel("Новое имя:"))
        layout.addWidget(self.newNameEdit)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("ОК")
        cancel_button = QPushButton("Отмена")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        ok_button.clicked.connect(self.on_ok_clicked)
        cancel_button.clicked.connect(self.reject)

    def getNames(self):
        return self.oldNameEdit.text().strip(), self.newNameEdit.text().strip()

    def on_ok_clicked(self):
        oldName, newName = self.getNames()

        if not oldName or not newName:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните оба поля.")
            return
        self.old_name = oldName 
        self.new_name = newName 

        self.accept()  



class ToolTipWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        self.gif_label = QLabel()
        self.text_label = QLabel()
        
        layout.addWidget(self.gif_label)
        layout.addWidget(self.text_label)
        self.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 10px;
        """)
        self.tooltips = {}
        self.setup_tooltips()

    def setup_tooltips(self):
        # Конфигурация подсказок
        tooltip_data = {
            "add_user_btn": {
                "text": "Добавление нового пользователя в систему\n"
                        "Требуется: веб-камера и хорошее освещение",
                "gif": "animations/add_user.gif"
            },
            "recognize_btn": {
                "text": "Распознавание лица в реальном времени\n"
                        "Убедитесь, что лицо находится в центре кадра",
                "gif": "animations/recognize.gif"
            },
            "rename_btn":{
                "text": "Переименовать пользователя\n"
                    "Введите старое и новое имя пользователя",
                "gif": "animations/rename.gif"
            },
            "delete_btn":{
                "text": "Удалить пользователя\n"
                        "Введите имя пользователя, которого хотите удалить",
                "gif": "animations/delete.gif"
            }

        }

        for btn_name, data in tooltip_data.items():
            btn = getattr(self, btn_name)
            tooltip = ToolTipWidget(self)
            
            # Загрузка гифки
            movie = QMovie(data["gif"])
            movie.setScaledSize(QSize(80, 80))
            tooltip.gif_label.setMovie(movie)
            
            # Настройка текста
            tooltip.text_label.setText(data["text"])
            tooltip.text_label.setStyleSheet("color: #444; font-size: 12px;")
            tooltip.text_label.setWordWrap(True)
            
            self.tooltips[btn] = {"widget": tooltip, "movie": movie}

        # Таймер для плавного появления
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)

    def enterEvent(self, event):
        widget = self.childAt(event.pos())
        if widget in self.tooltips:
            self.current_tooltip = self.tooltips[widget]
            self.tooltip_timer.start(500)  # Задержка 0.5 сек

    def leaveEvent(self, event):
        self.tooltip_timer.stop()
        if hasattr(self, 'current_tooltip'):
            self.hide_tooltip()

    def show_tooltip(self):
        if hasattr(self, 'current_tooltip'):
            btn = self.sender() if self.sender() else None
            pos = self.mapToGlobal(btn.pos())
            tooltip = self.current_tooltip["widget"]
            tooltip.move(pos.x() + btn.width() + 10, pos.y())
            tooltip.show()
            self.current_tooltip["movie"].start()

    def hide_tooltip(self):
        self.current_tooltip["widget"].hide()
        self.current_tooltip["movie"].stop()
        del self.current_tooltip

class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система распознавания лиц")
        self.setWindowIcon(QIcon("icons/face.png"))
        self.setFixedSize(500, 600)
        self.tooltips = {}
        self.setup_ui()
        self.setup_styles()
        self.setup_animations()
        self.setup_tooltips()  # Добавляем инициализацию подсказок

    def setup_tooltips(self):
        tooltip_data = {
            self.add_user_btn: {
                "text": "Добавление нового пользователя в систему\n"
                        "Требуется: веб-камера и хорошее освещение",
                "gif": "animations/add.gif"
            },
            self.recognize_btn: {
                "text": "Распознавание лица в реальном времени\n"
                        "Убедитесь, что лицо находится в центре кадра",
                "gif": "animations/recognize.gif"
            },
            self.rename_btn:{
                "text": "Переименовать пользователя\n"
                        "Введите старое и новое имя пользователя",
                "gif": "animations/rename.gif"
            },
            self.delete_btn:{
                "text": "Удалить пользователя\n"
                        "Введите имя пользователя, которого хотите удалить",
                "gif": "animations/delete.gif"
            }
        }

        for btn, data in tooltip_data.items():
            tooltip = QWidget(self, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
            tooltip.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            layout = QHBoxLayout(tooltip)
            
            # Загрузка гифки
            gif_label = QLabel()
            movie = QMovie(data["gif"])
            movie.setScaledSize(QSize(80, 80))
            gif_label.setMovie(movie)
            
            # Текст подсказки
            text_label = QLabel(data["text"])
            text_label.setStyleSheet("color: #444; font-size: 12px; padding: 5px;")
            text_label.setWordWrap(True)
            
            layout.addWidget(gif_label)
            layout.addWidget(text_label)
            tooltip.setStyleSheet("""
                background-color: #f8f9fa;  /* Изменен цвет фона */
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #dee2e6;  /* Добавлена граница */
            """)
            
            self.tooltips[btn] = {"widget": tooltip, "movie": movie}

        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            if obj in self.tooltips:
                self.current_btn = obj
                self.tooltip_timer.start(500)
        elif event.type() == QEvent.Type.Leave:
            self.tooltip_timer.stop()
            if hasattr(self, 'current_tooltip'):
                self.hide_tooltip()
        return super().eventFilter(obj, event)

    def show_tooltip(self):
        if self.current_btn in self.tooltips:
            tooltip_data = self.tooltips[self.current_btn]
            btn_pos = self.current_btn.mapToGlobal(QPoint(0, 0))
            tooltip_y = btn_pos.y() - 35  # Смещение выше кнопки
            tooltip_x = btn_pos.x() + self.current_btn.width()  # Центрирование
            tooltip_data["widget"].move(tooltip_x + 10, tooltip_y)
            tooltip_data["widget"].show()
            tooltip_data["movie"].start()
            self.current_tooltip = tooltip_data

    def hide_tooltip(self):
        if hasattr(self, 'current_tooltip'):
            self.current_tooltip["widget"].hide()
            self.current_tooltip["movie"].stop()
            del self.current_tooltip

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(25)

        # Header with decorative element
        self.title_label = QLabel("Система распознавания лиц")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Buttons with icons
        self.add_user_btn = QPushButton("Добавить пользователя")
        self.recognize_btn = QPushButton("Распознать пользователя")
        self.rename_btn = QPushButton("Переименовать пользователя")
        self.delete_btn = QPushButton("Удалить пользователя")
        self.exit_btn = QPushButton("Выход")
        for btn in [self.add_user_btn, self.recognize_btn,self.rename_btn,self.delete_btn]:
            btn.installEventFilter(self)

        # Set button properties
        for btn in [self.add_user_btn, self.recognize_btn, self.rename_btn, self.delete_btn, self.exit_btn]:
            btn.setMinimumSize(300, 60)
            btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
            btn.setIconSize(QSize(28, 28))


        layout.addStretch(1)
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.add_user_btn)
        layout.addWidget(self.recognize_btn)
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.exit_btn)
        layout.addStretch(2)

        # Connect signals
        self.add_user_btn.clicked.connect(self.add_user)
        self.recognize_btn.clicked.connect(self.recognize_user)
        self.rename_btn.clicked.connect(self.open_rename_dialog)
        self.delete_btn.clicked.connect(self.delete_user)
        self.exit_btn.clicked.connect(self.close)

    def setup_styles(self):
        # Modern color palette
        self.bg_color = QColor(245, 241, 235)    # Warm white
        self.primary = QColor(190, 175, 210)     # Soft blue
        self.secondary = QColor(220, 186, 200)   # Muted pink
        self.accent = QColor(190, 175, 210)      
        self.text_color = QColor(70, 70, 70)    # Dark gray

        # Background gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.bg_color)
        gradient.setColorAt(1, self.bg_color.darker(102))

        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)

        # Title style
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 26px;
                font-weight: bold;
                margin-bottom: 40px;
            }}
        """)

        # Button styles
        btn_style = """
            QPushButton {{
                color: {text_color};
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 12px 25px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-color: {hover_border};
                padding: 14px 27px;
            }}
            QPushButton:pressed {{
                background-color: {press_color};
            }}
        """

        # Set individual styles
        self.add_user_btn.setStyleSheet(btn_style.format(
            text_color=self.text_color.name(),
            bg_color=self.primary.lighter(115).name(),
            border_color=self.primary.darker(110).name(),
            hover_color=self.primary.lighter(105).name(),
            hover_border=self.primary.darker(115).name(),
            press_color=self.primary.name()
        ))

        self.recognize_btn.setStyleSheet(btn_style.format(
            text_color=self.text_color.name(),
            bg_color=self.accent.lighter(115).name(),
            border_color=self.accent.darker(110).name(),
            hover_color=self.accent.lighter(105).name(),
            hover_border=self.accent.darker(115).name(),
            press_color=self.accent.name()
        ))

        self.rename_btn.setStyleSheet(btn_style.format(
            text_color=self.text_color.name(),
            bg_color=self.accent.lighter(115).name(),
            border_color=self.accent.darker(110).name(),
            hover_color=self.accent.lighter(105).name(),
            hover_border=self.accent.darker(115).name(),
            press_color=self.accent.name()
        ))

        self.delete_btn.setStyleSheet(btn_style.format(
            text_color=self.text_color.name(),
            bg_color=self.accent.lighter(115).name(),
            border_color=self.accent.darker(110).name(),
            hover_color=self.accent.lighter(105).name(),
            hover_border=self.accent.darker(115).name(),
            press_color=self.accent.name()
        ))

        self.exit_btn.setStyleSheet(btn_style.format(
            text_color=self.text_color.name(),
            bg_color=self.secondary.lighter(115).name(),
            border_color=self.secondary.darker(110).name(),
            hover_color=self.secondary.lighter(105).name(),
            hover_border=self.secondary.darker(115).name(),
            press_color=self.secondary.name()
        ))

    def setup_animations(self):
        # Hover animations
        for btn in [self.add_user_btn, self.recognize_btn,self.rename_btn,self.delete_btn, self.exit_btn]:
            anim = QPropertyAnimation(btn, b"geometry")
            anim.setDuration(200)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            btn.enterEvent = lambda event, b=btn: self.animate_button(b, 5)
            btn.leaveEvent = lambda event, b=btn: self.animate_button(b, -5)

    def animate_button(self, button, offset):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        current = button.geometry()
        anim.setStartValue(current)
        anim.setEndValue(current.adjusted(-offset, -offset, offset, offset))
        anim.start()

    def add_user(self):
        name, ok = QInputDialog.getText(self, "Ввод имени", "Введите имя пользователя:")
        if ok and name:
            try:
                result = subprocess.run([sys.executable, "face_gen.py", name], capture_output=True, text=True)
                if result.returncode != 0:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при распознавании пользователя:\n{result.stderr}")
                else:
                    result1 = subprocess.run([sys.executable, "face_training.py"], capture_output=True, text=True)
                    if result1.returncode != 0:
                        QMessageBox.critical(self, "Ошибка", f"Ошибка при тренировке:\n{result1.stderr}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить операцию: {str(e)}")
                
    def recognize_user(self):
        try:
            result = subprocess.run([sys.executable, "face_detect.py"], capture_output=True, text=True)
            if result.returncode != 0:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при распознавании пользователя:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить операцию: {str(e)}")

    def open_rename_dialog(self):
        try:
            self.rename_dialog = RenameDialog(self)
            self.rename_dialog.accepted.connect(self.rename_user)
            self.rename_dialog.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть диалоговое окно: {str(e)}")

    def rename_user(self):
        try:
            oldName = self.rename_dialog.old_name
            newName = self.rename_dialog.new_name
            result = subprocess.run([sys.executable, "rename.py", oldName, newName], capture_output=True, text=True)
            if result.returncode != 0:  # Если код возврата не 0, это ошибка
                QMessageBox.critical(self, "Ошибка", f"Ошибка при переименовании пользователя:\n{result.stderr}")
            else:
                QMessageBox.information(self, "Успех", f"Пользователь {oldName} успешно переименован в {newName}." )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось выполнить операцию переименования: {str(e)}"
            )

    def delete_user(self):
        name, ok = QInputDialog.getText(self, "Ввод имени для удаления", "Введите имя пользователя:")
        if ok and name:
            try:
                from delete import delete_user
                success, message = delete_user(name)
                
                if success:
                    QMessageBox.information(self, "Успех",  message)
                else:
                    QMessageBox.critical(self, "Ошибка", message)
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить операцию: {str(e)}")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec())

    

