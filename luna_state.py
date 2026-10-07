from enum import Enum

from PySide6.QtCore import QObject, Signal


class LunaState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"


class LunaStateManager(QObject):
    state_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = LunaState.IDLE

    @property
    def state(self):
        return self._state

    def set_state(self, state: LunaState):
        if not isinstance(state, LunaState):
            raise TypeError("state must be a LunaState")

        if self._state == state:
            return

        self._state = state
        self.state_changed.emit(state)

    def reset(self):
        self.set_state(LunaState.IDLE)