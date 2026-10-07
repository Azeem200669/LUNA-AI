from PySide6.QtCore import QObject, Signal, QThread

from core.agent import LunaAgent


class AIWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, message: str, model: str = "auto"):
        super().__init__()

        self.message = message
        self.model = model

    def run(self):
        try:
            luna = LunaAgent()

            response = luna.chat(
                self.message,
                model=self.model
            )

            if not response:
                response = "I didn't receive a response."

            self.finished.emit(str(response))

        except Exception as exc:
            self.error.emit(str(exc))


class AIEngine(QObject):
    response_ready = Signal(str)
    error = Signal(str)
    started = Signal()
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.thread = None
        self.worker = None

    def ask(self, message: str, model: str = "auto"):
        message = message.strip()

        if not message:
            self.error.emit("Please enter a message.")
            return

        # Prevent starting another request while one is running.
        if self.thread is not None and self.thread.isRunning():
            self.error.emit(
                "LUNA is still processing the previous request."
            )
            return

        self.thread = QThread()
        self.worker = AIWorker(
            message=message,
            model=model
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.started)
        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(
            self._handle_success
        )

        self.worker.error.connect(
            self._handle_error
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self._thread_finished
        )

        self.thread.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.start()

    def _handle_success(self, response: str):
        self.response_ready.emit(response)
        self.finished.emit()

    def _handle_error(self, message: str):
        self.error.emit(message)
        self.finished.emit()

    def _thread_finished(self):
        self.worker = None
        self.thread = None