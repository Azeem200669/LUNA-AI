STYLE = """

/* =========================================================
   MAIN WINDOW
========================================================= */

QMainWindow {
    background: #02060c;
}

QWidget {
    font-family: "Segoe UI";
    color: #e8fbff;
}


/* =========================================================
   HEADER
========================================================= */

QLabel#Title {
    color: #f5ffff;
    font-size: 30px;
    font-weight: 700;
}

QLabel#Subtitle {
    color: #486878;
    font-size: 14px;
}

QLabel#Status {
    color: #00eaff;
    font-size: 13px;
    font-weight: 700;
}


/* =========================================================
   CONVERSATION PANEL
========================================================= */

QFrame#MessagePanel {
    background: #06101a;
    border: 1px solid #173140;
    border-radius: 24px;
}


/* =========================================================
   MESSAGE INPUT FRAME
========================================================= */

QFrame#InputFrame {
    background: #07111a;
    border: 1px solid #17333f;
    border-radius: 18px;
}


/* =========================================================
   INPUT
========================================================= */

QLineEdit {
    background: transparent;
    color: #eaffff;
    border: none;
    padding: 0 12px;
    font-size: 14px;
}

QLineEdit:focus {
    border: none;
}

QLineEdit::placeholder {
    color: #56717f;
}


/* =========================================================
   VOICE BUTTON
========================================================= */

QPushButton#VoiceButton {
    background: #071923;
    color: #00eaff;
    border: 1px solid #194351;
    border-radius: 14px;
    font-size: 19px;
}

QPushButton#VoiceButton:hover {
    background: #0c2530;
    border: 1px solid #00eaff;
}

QPushButton#VoiceButton:pressed {
    background: #0e3946;
}


/* =========================================================
   SEND BUTTON
========================================================= */

QPushButton#SendButton {
    background: #09c5e7;
    color: #031017;
    border: none;
    border-radius: 14px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton#SendButton:hover {
    background: #2dd8f5;
}

QPushButton#SendButton:pressed {
    background: #089db9;
}

QPushButton#SendButton:disabled {
    background: #19333d;
    color: #5e747e;
}


/* =========================================================
   DISABLED VOICE
========================================================= */

QPushButton#VoiceButton:disabled {
    background: #0b151c;
    color: #3c5c68;
    border: 1px solid #15272f;
}


/* =========================================================
   SCROLL
========================================================= */

QScrollBar:vertical {
    width: 5px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #123746;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #00cfe8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}


/* =========================================================
   🌙 LUNA STYLE EXTENSIONS — APPENDED ONLY
   (everything above is unchanged; new selectors use new
    object names, so no existing widget is affected)
========================================================= */


/* =========================================================
   GLOBAL TEXT SELECTION
========================================================= */

QWidget {
    selection-background-color: #0c2530;
    selection-color: #00eaff;
}


/* =========================================================
   WINDOW CONTROL BUTTONS (frameless title bar)
========================================================= */

QPushButton#WindowButton {
    background: transparent;
    color: #486878;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    padding: 4px 12px;
}

QPushButton#WindowButton:hover {
    background: #0c2530;
    color: #00eaff;
}

QPushButton#WindowButton:pressed {
    background: #0e3946;
}

QPushButton#CloseButton {
    background: transparent;
    color: #486878;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    padding: 4px 12px;
}

QPushButton#CloseButton:hover {
    background: #33101c;
    color: #ff6b81;
}

QPushButton#CloseButton:pressed {
    background: #431524;
}

QPushButton#SettingsButton {
    background: transparent;
    color: #486878;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    padding: 4px 10px;
}

QPushButton#SettingsButton:hover {
    background: #0c2530;
    color: #00eaff;
}


/* =========================================================
   STATUS LABEL VARIANTS
   (matches the LunaCorePro state colors)
========================================================= */

QLabel#StatusSuccess {
    color: #5aff96;
}

QLabel#StatusError {
    color: #ff5f5f;
}

QLabel#StatusAlert {
    color: #ffa046;
}

QLabel#StatusProcessing {
    color: #ffc85a;
}

QLabel#StatusSleep {
    color: #6e8296;
}


/* =========================================================
   VOICE BUTTON LISTENING STATE
   (set property "active" to True and repolish)
========================================================= */

QPushButton#VoiceButton[active="true"] {
    background: #06301f;
    color: #5aff96;
    border: 1px solid #2bd97f;
}

QPushButton#VoiceButton[active="true"]:hover {
    background: #0a4029;
}

QPushButton#VoiceButton[active="true"]:pressed {
    background: #0c4d31;
}


/* =========================================================
   CHAT BUBBLES
========================================================= */

QFrame#BubbleUser {
    background: #0a2a36;
    border: 1px solid #124a5c;
    border-radius: 16px;
}

QFrame#BubbleLuna {
    background: #0a141f;
    border: 1px solid #173140;
    border-radius: 16px;
}

QLabel#BubbleSenderUser {
    color: #00eaff;
    font-size: 11px;
    font-weight: 700;
}

QLabel#BubbleSenderLuna {
    color: #9fdce8;
    font-size: 11px;
    font-weight: 700;
}

QLabel#BubbleText {
    background: transparent;
    font-size: 14px;
}

QLabel#BubbleTime {
    color: #3c5c68;
    font-size: 10px;
}


/* =========================================================
   QUICK ACTION CHIPS
========================================================= */

QPushButton#Chip {
    background: #071923;
    color: #9fdce8;
    border: 1px solid #194351;
    border-radius: 14px;
    padding: 6px 14px;
    font-size: 12px;
}

QPushButton#Chip:hover {
    background: #0c2530;
    color: #00eaff;
    border: 1px solid #00eaff;
}

QPushButton#Chip:pressed {
    background: #0e3946;
}

QPushButton#Chip:checked {
    background: #063544;
    color: #00eaff;
    border: 1px solid #00eaff;
}

QPushButton#Chip:disabled {
    background: #0b151c;
    color: #3c5c68;
    border: 1px solid #15272f;
}


/* =========================================================
   TASK PROGRESS BAR
========================================================= */

QProgressBar#TaskProgress {
    background: #07111a;
    border: 1px solid #17333f;
    border-radius: 9px;
    min-height: 14px;
    max-height: 14px;
    text-align: center;
    color: #56717f;
    font-size: 9px;
    font-weight: 700;
}

QProgressBar#TaskProgress::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #089db9,
        stop:1 #00eaff
    );
    border-radius: 8px;
}


/* =========================================================
   BUSY BAR (indeterminate "thinking" pulse)
========================================================= */

QProgressBar#BusyBar {
    background: #07111a;
    border: 1px solid #17333f;
    border-radius: 9px;
    min-height: 14px;
    max-height: 14px;
}

QProgressBar#BusyBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #02060c,
        stop:0.5 #00eaff,
        stop:1 #02060c
    );
    border-radius: 8px;
    margin: 2px;
}


/* =========================================================
   SLIDER (volume / brightness)
========================================================= */

QSlider::groove:horizontal {
    height: 6px;
    background: #07111a;
    border: 1px solid #17333f;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #089db9,
        stop:1 #00eaff
    );
    border-radius: 3px;
}

QSlider::add-page:horizontal {
    background: #0a141d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    background: #00eaff;
}

QSlider::handle:horizontal:hover {
    background: #2dd8f5;
}

QSlider::handle:horizontal:pressed {
    background: #089db9;
}

QSlider::groove:vertical {
    width: 6px;
    background: #07111a;
    border: 1px solid #17333f;
    border-radius: 3px;
}

QSlider::handle:vertical {
    height: 16px;
    width: 16px;
    margin: 0 -6px;
    border-radius: 8px;
    background: #00eaff;
}


/* =========================================================
   CHECKBOXES
========================================================= */

QCheckBox {
    color: #9fdce8;
    font-size: 13px;
    spacing: 8px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #194351;
    border-radius: 6px;
    background: #071923;
}

QCheckBox::indicator:hover {
    border: 1px solid #00eaff;
}

QCheckBox::indicator:checked {
    background: #00eaff;
    border: 1px solid #00eaff;
}

QCheckBox:disabled {
    color: #3c5c68;
}

QCheckBox::indicator:disabled {
    background: #0b151c;
    border: 1px solid #15272f;
}


/* =========================================================
   COMBO BOX
========================================================= */

QComboBox {
    background: #071923;
    color: #eaffff;
    border: 1px solid #194351;
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #00eaff;
}

QComboBox:disabled {
    color: #3c5c68;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}

QComboBox::down-arrow {
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #00eaff;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background: #06101a;
    color: #eaffff;
    border: 1px solid #173140;
    border-radius: 10px;
    padding: 4px;
    outline: none;
    selection-background-color: #0c2530;
    selection-color: #00eaff;
}


/* =========================================================
   CONTEXT MENU
========================================================= */

QMenu {
    background: #06101a;
    border: 1px solid #173140;
    border-radius: 12px;
    padding: 6px;
}

QMenu::item {
    color: #e8fbff;
    padding: 8px 26px;
    border-radius: 8px;
    font-size: 13px;
}

QMenu::item:selected {
    background: #0c2530;
    color: #00eaff;
}

QMenu::item:disabled {
    color: #3c5c68;
}

QMenu::separator {
    height: 1px;
    background: #173140;
    margin: 6px 10px;
}


/* =========================================================
   TOOLTIPS
========================================================= */

QToolTip {
    background: #0c2530;
    color: #baf3ff;
    border: 1px solid #00eaff;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}


/* =========================================================
   CHAT TEXT DISPLAY
========================================================= */

QTextBrowser,
QTextEdit,
QPlainTextEdit {
    background: transparent;
    color: #e8fbff;
    border: none;
    font-size: 14px;
}


/* =========================================================
   SCROLL AREA + HORIZONTAL SCROLLBAR
========================================================= */

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:horizontal {
    height: 5px;
    background: transparent;
}

QScrollBar::handle:horizontal {
    background: #123746;
    border-radius: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: #00cfe8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}


/* =========================================================
   BUTTON VARIANTS
========================================================= */

QPushButton#GhostButton {
    background: transparent;
    color: #9fdce8;
    border: 1px solid #194351;
    border-radius: 14px;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton#GhostButton:hover {
    background: #071923;
    color: #00eaff;
    border: 1px solid #00eaff;
}

QPushButton#GhostButton:pressed {
    background: #0e3946;
}

QPushButton#GhostButton:disabled {
    color: #3c5c68;
    border: 1px solid #15272f;
}

QPushButton#DangerButton {
    background: #2a0e14;
    color: #ff8095;
    border: 1px solid #57202c;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 18px;
}

QPushButton#DangerButton:hover {
    background: #3a1220;
    color: #ff5f5f;
    border: 1px solid #ff5f5f;
}

QPushButton#DangerButton:pressed {
    background: #4a1524;
}

QPushButton#SuccessButton {
    background: #07271a;
    color: #5aff96;
    border: 1px solid #1d5c3c;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 18px;
}

QPushButton#SuccessButton:hover {
    background: #0a3a25;
    color: #7dffb4;
    border: 1px solid #2bd97f;
}

QPushButton#SuccessButton:pressed {
    background: #0c4d31;
}

QPushButton#IconButton {
    background: transparent;
    color: #486878;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    padding: 6px;
}

QPushButton#IconButton:hover {
    background: #0c2530;
    color: #00eaff;
}

QPushButton#IconButton:pressed {
    background: #0e3946;
}


/* =========================================================
   SETTINGS SIDE PANEL
========================================================= */

QFrame#SidePanel {
    background: #050d15;
    border: 1px solid #12242e;
    border-radius: 20px;
}

QLabel#PanelTitle {
    color: #9fdce8;
    font-size: 15px;
    font-weight: 700;
}

QLabel#SectionLabel {
    color: #56717f;
    font-size: 11px;
    font-weight: 700;
}


/* =========================================================
   SMALL EXTRAS
========================================================= */

QFrame#Divider {
    background: #12242e;
    border: none;
    max-height: 1px;
}

QLabel#Clock {
    color: #9fdce8;
    font-size: 13px;
    font-weight: 600;
}

QLabel#ThinkingDots {
    color: #b97dff;
    font-size: 14px;
    font-weight: 700;
}

"""