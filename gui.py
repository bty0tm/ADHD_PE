import sys
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFontDatabase, QIntValidator
from PySide6.QtUiTools import QUiLoader

from backend import ADHD_Backend
from timer import Timer


class MatchaApp:
    def __init__(self):
        # 1. Шрифты и Интерфейс
        QFontDatabase.addApplicationFont("Intro.otf")
        loader = QUiLoader()
        self.ui = loader.load("focus.ui")
        self.ui.setWindowTitle("Green Focus App 🌿")
        self.ui.screen_manager.setCurrentIndex(0)

        # 2. Инициализация логики
        self.engine = ADHD_Backend()  # Мозг
        self.timer_logic = Timer()  # Двигатель

        self.current_task_index = 0
        self.time_left = 0
        self.is_break = False

        # 3. GUI Таймер (Пульс приложения)
        self.gui_timer = QTimer(self.ui)
        self.gui_timer.timeout.connect(self.hidden_timer_tick)

        # 4. Настройка полей ввода
        self.setup_ui_elements()

        # 5. Привязка кнопок
        self.setup_connections()

    def setup_ui_elements(self):
        validator = QIntValidator(1, 99, self.ui)
        self.ui.input_work.setValidator(validator)
        self.ui.input_break.setValidator(validator)
        self.ui.input_work.setText("25")
        self.ui.input_break.setText("5")
        # Центрирование текста
        for lbl in [self.ui.label_2, self.ui.label_3, self.ui.title_name,
                    self.ui.input_work, self.ui.input_break]:
            lbl.setAlignment(Qt.AlignCenter)

    def setup_connections(self):
        self.ui.btn_start_app.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(1))
        self.ui.btn_back.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(0))
        self.ui.btn_generate.clicked.connect(self.generate_tasks)
        self.ui.btn_open_time_settings.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(2))
        self.ui.btn_save_time.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(1))
        self.ui.btn_hint.clicked.connect(self.show_time_hint)
        self.ui.btn_start_focus.clicked.connect(self.start_focus_session)
        self.ui.btn_stop_focus.clicked.connect(self.stop_focus_session)

    def show_time_hint(self):
        msg = QMessageBox(self.ui)
        msg.setWindowTitle("Советы 🌿")
        msg.setText(
            "<b>25/5</b> — классический режим, установлено по умолчанию;<br>"
            "<b>30/10</b> — классика для небольших учебных задач;<br>"
            "<b>45/10</b> — классика для учебы;<br>"
            "<b>50/15</b> — серьезные задачи, углубленное обучение.<br><br>"
            "Не бойтесь экспериментировать, все получится! (⌒▽⌒)♡"
        )

        msg.setStyleSheet("""
                    QMessageBox { 
                        background-color: #eaffe1; 
                    }
                    QLabel { 
                        color: #3d2500; 
                        font-size: 13px; 
                    }
                    QPushButton {
                        background-color: #bfecac; 
                        color: #3d2500;
                        border-radius: 10px; 
                        font-weight: bold;
                        border: 1px solid #a3d98d;

                        /* Центрирование текста внутри кнопки OK */
                        min-width: 70px;
                        min-height: 25px;
                        padding: 0px; 
                        text-align: center; 
                    }
                    QPushButton:hover {
                        background-color: #a8dba1;
                    }
                """)
        msg.exec()

    def generate_tasks(self):
        task_text = self.ui.task_input.text()
        if not task_text.strip(): return

        work_mins = int(self.ui.input_work.text() or 25)

        # 1. Сначала отключаем кнопку и чистим старые задачи
        self.ui.btn_generate.setEnabled(False)
        self.clear_tasks_layout()

        # 2. ВОТ ОНА! Добавляем надпись об ожидании
        temp_lbl = QLabel("НЕЙРОСЕТЬ СОСТАВЛЯЕТ ПЛАН... ૮ ˶• ༝ •˶ა")
        temp_lbl.setAlignment(Qt.AlignCenter)
        # Можно добавить немного стиля прямо здесь, если хочешь
        temp_lbl.setStyleSheet("color: #3d2500;")
        self.ui.tasks_layout.addWidget(temp_lbl)

        # 3. КРИТИЧНО: Заставляем Qt перерисовать интерфейс ПРЯМО СЕЙЧАС
        # Без этой строчки надпись появится только КОГДА нейросеть уже ответит
        QApplication.processEvents()

        # 4. Запускаем ИИ
        success, tasks = self.engine.generate_initial_plan(task_text, work_mins)

        # 5. Убираем надпись "думает" (чистим слой перед выводом реальных задач)
        self.clear_tasks_layout()

        if success:
            self.clear_tasks_layout()
            for task in tasks:
                self.ui.tasks_layout.addWidget(QLabel(f"• {task}"))
            self.ui.btn_start_focus.setEnabled(True)

        self.ui.btn_generate.setEnabled(True)

    def clear_tasks_layout(self):
        while self.ui.tasks_layout.count():
            child = self.ui.tasks_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

    def start_focus_session(self):
        # Синхронизируем время перед стартом
        self.timer_logic.set_durations(self.ui.input_work.text(), self.ui.input_break.text())

        self.current_task_index = 0
        self.is_break = False
        self.time_left = self.timer_logic.work_duration

        self.ui.screen_manager.setCurrentIndex(3)
        self.update_status_ui()

        self.engine.start_blocking()
        self.gui_timer.start(1000)

    def hidden_timer_tick(self):
        if self.time_left > 0:
            self.time_left -= 1
        else:
            if not self.is_break:
                # Переход на отдых
                self.is_break = True
                self.time_left = self.timer_logic.break_duration
                self.engine.stop_blocking()
            else:
                # Возврат к работе
                self.is_break = False
                self.current_task_index += 1
                if self.current_task_index >= len(self.engine.subtasks_list):
                    self.finish_app()
                    return
                self.time_left = self.timer_logic.work_duration
                self.engine.start_blocking()

        self.update_status_ui()

    def update_status_ui(self):
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        if self.is_break:
            status = f"ОТДЫХ\n{time_str}"
        else:
            task = self.engine.subtasks_list[self.current_task_index] if self.current_task_index < len(
                self.engine.subtasks_list) else "..."
            status = f"В ФОКУСЕ:\n{task}\n\n⏱ {time_str}"
        self.ui.lbl_timer_display.setText(status)

    def stop_focus_session(self):
        self.gui_timer.stop()
        self.engine.stop_blocking()
        self.ui.screen_manager.setCurrentIndex(1)

    def finish_app(self):
        self.gui_timer.stop()
        self.engine.stop_blocking()
        self.ui.lbl_timer_display.setText("ГОТОВО! ✨")
        QTimer.singleShot(3000, lambda: self.ui.screen_manager.setCurrentIndex(0))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MatchaApp()
    window.ui.show()
    sys.exit(app.exec())