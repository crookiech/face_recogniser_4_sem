import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система распознавания лиц")
        self.setFixedSize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        title_label = QLabel("Система распознавания лиц")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.add_user_btn = QPushButton("Добавить пользователя")
        self.add_user_btn.setFixedSize(200, 50)
        self.add_user_btn.clicked.connect(self.add_user)
        layout.addWidget(self.add_user_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.recognize_btn = QPushButton("Распознать пользователя")
        self.recognize_btn.setFixedSize(200, 50)
        self.recognize_btn.clicked.connect(self.recognize_user)
        layout.addWidget(self.recognize_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.exit_btn = QPushButton("Выход")
        self.exit_btn.setFixedSize(200, 50)
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec())