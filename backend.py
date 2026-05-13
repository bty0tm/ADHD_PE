import threading
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taskSplitter import split_tasks
from block_structure.process_block import kill_apps
from block_structure.sites_block import redirect_browser


class ADHD_Backend:
    def __init__(self):
        self.is_blocking = False
        self.subtasks_list = []
        self.original_task = ""

    # Блокировка в потоке, чтобы все приложение не встало и работал таймер
    def start_blocking(self):
        if self.is_blocking: return
        self.is_blocking = True

        def block_loop():
            while self.is_blocking:
                try:
                    redirect_browser()
                    kill_apps()
                except Exception:
                    pass
                time.sleep(2)

        threading.Thread(target=block_loop, daemon=True).start()

    def stop_blocking(self):
        self.is_blocking = False

    # Связывается с tasksplitter-ом, чтобы разбить задачи нейронкой
    def generate_initial_plan(self, task_text, work_mins):
        self.original_task = task_text
        subtasks = split_tasks(self.original_task, work_mins)

        if subtasks and not subtasks[0].startswith("Произошла ошибка"):
            self.subtasks_list = subtasks
            return True, self.subtasks_list
        return False, subtasks