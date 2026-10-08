class LunaState:

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

    current = IDLE

    @classmethod
    def set(cls, state):
        cls.current = state
        print(f"🌙 LUNA STATE: {state.upper()}")