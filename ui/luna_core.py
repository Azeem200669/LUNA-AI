import math
import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QConicalGradient
)
from PySide6.QtWidgets import QWidget


class LunaCore(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(520, 520)

        # -----------------------------
        # LUNA STATE
        # -----------------------------

        self.state = "idle"

        # -----------------------------
        # ANIMATION
        # -----------------------------

        self.rotation = 0.0
        self.rotation2 = 0.0
        self.rotation3 = 0.0
        self.pulse = 0.0

        # -----------------------------
        # PARTICLES
        # -----------------------------

        self.particles = []

        for _ in range(110):

            self.particles.append({
                "angle": random.uniform(0, 360),
                "radius": random.uniform(120, 235),
                "speed": random.uniform(0.03, 0.14),
                "size": random.uniform(1.0, 2.5),
                "alpha": random.randint(70, 190),
                "offset": random.uniform(0, 6.28)
            })

        # -----------------------------
        # TIMER
        # -----------------------------

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(16)

    # =========================================================
    # STATE
    # =========================================================

    def set_state(self, state):

        self.state = str(
            state
        ).lower()

        self.update()

    # =========================================================
    # ANIMATION
    # =========================================================

    def animate(self):

        self.rotation += 0.35
        self.rotation2 -= 0.22
        self.rotation3 += 0.12

        self.pulse += 0.055

        for particle in self.particles:

            particle["angle"] += particle["speed"]

            if particle["angle"] >= 360:
                particle["angle"] -= 360

        self.update()

    # =========================================================
    # DRAW GLOW
    # =========================================================

    def draw_glow(
        self,
        painter,
        x,
        y,
        radius,
        alpha
    ):

        gradient = QRadialGradient(
            x,
            y,
            radius
        )

        gradient.setColorAt(
            0.0,
            QColor(
                0,
                240,
                255,
                alpha
            )
        )

        gradient.setColorAt(
            0.35,
            QColor(
                0,
                190,
                240,
                int(alpha * 0.45)
            )
        )

        gradient.setColorAt(
            1.0,
            QColor(
                0,
                100,
                180,
                0
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QBrush(gradient)
        )

        painter.drawEllipse(
            int(x - radius),
            int(y - radius),
            int(radius * 2),
            int(radius * 2)
        )

    # =========================================================
    # PAINT
    # =========================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        width = self.width()
        height = self.height()

        cx = width / 2
        cy = height / 2 - 10

        scale = min(
            width,
            height
        ) / 620

        # =====================================================
        # BACKGROUND
        # =====================================================

        painter.fillRect(
            self.rect(),
            QColor("#02070D")
        )

        # =====================================================
        # HUGE SOFT ATMOSPHERIC GLOW
        # =====================================================

        self.draw_glow(
            painter,
            cx,
            cy,
            270 * scale,
            35
        )

        self.draw_glow(
            painter,
            cx,
            cy,
            190 * scale,
            25
        )

        # =====================================================
        # BACKGROUND STARS
        # =====================================================

        painter.setPen(
            Qt.NoPen
        )

        for particle in self.particles:

            angle = math.radians(
                particle["angle"]
            )

            radius = (
                particle["radius"]
                * scale
            )

            x = (
                cx
                + math.cos(angle)
                * radius
            )

            y = (
                cy
                + math.sin(angle)
                * radius
            )

            size = (
                particle["size"]
                * scale
            )

            painter.setBrush(
                QColor(
                    20,
                    210,
                    245,
                    particle["alpha"]
                )
            )

            painter.drawEllipse(
                int(x - size),
                int(y - size),
                int(size * 2),
                int(size * 2)
            )

        # =====================================================
        # OUTER CIRCULAR HALO
        # =====================================================

        painter.setBrush(
            Qt.NoBrush
        )

        outer_rings = [
            (235, 28, 1.0),
            (220, 38, 1.0),
            (205, 50, 1.0),
            (190, 65, 1.2),
            (175, 80, 1.3)
        ]

        for radius, alpha, thickness in outer_rings:

            r = radius * scale

            pen = QPen(
                QColor(
                    0,
                    210,
                    245,
                    alpha
                )
            )

            pen.setWidthF(
                thickness
            )

            painter.setPen(
                pen
            )

            painter.drawEllipse(
                int(cx - r),
                int(cy - r),
                int(r * 2),
                int(r * 2)
            )

        # =====================================================
        # ROTATING ARC SYSTEM
        # =====================================================

        arc_data = [

            (218, 20, 75, 150),

            (218, 190, 70, 140),

            (195, 70, 65, 130),

            (195, 250, 55, 110),

            (170, 10, 80, 160),

            (170, 205, 70, 140),

            (145, 45, 75, 150),

            (145, 235, 60, 120),

            (120, 100, 100, 200),

            (120, 285, 50, 100)
        ]

        for (
            radius,
            start,
            span,
            alpha
        ) in arc_data:

            r = radius * scale

            pen = QPen(
                QColor(
                    0,
                    235,
                    255,
                    alpha
                )
            )

            pen.setWidthF(
                1.4
            )

            painter.setPen(
                pen
            )

            animated_start = (
                start
                + self.rotation
            )

            painter.drawArc(
                int(cx - r),
                int(cy - r),
                int(r * 2),
                int(r * 2),
                int(animated_start * 16),
                int(span * 16)
            )

        # =====================================================
        # ORBITING GLOWING NODES
        # =====================================================

        orbit_data = [

            (220, 0, 4),
            (220, 120, 3),
            (220, 240, 3),

            (195, 50, 3),
            (195, 170, 4),
            (195, 290, 3),

            (170, 30, 3),
            (170, 145, 3),
            (170, 260, 4),

            (145, 80, 3),
            (145, 200, 3),
            (145, 320, 3),

            (120, 15, 3),
            (120, 135, 3),
            (120, 255, 3)
        ]

        for index, (
            radius,
            angle,
            size
        ) in enumerate(orbit_data):

            direction = (
                1
                if index % 2 == 0
                else -1
            )

            animated_angle = (
                angle
                + self.rotation2
                * direction
            )

            radians = math.radians(
                animated_angle
            )

            r = radius * scale

            x = (
                cx
                + math.cos(radians)
                * r
            )

            y = (
                cy
                + math.sin(radians)
                * r
            )

            dot_size = (
                size
                * scale
            )

            self.draw_glow(
                painter,
                x,
                y,
                dot_size * 5,
                80
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(
                    90,
                    245,
                    255,
                    235
                )
            )

            painter.drawEllipse(
                int(x - dot_size),
                int(y - dot_size),
                int(dot_size * 2),
                int(dot_size * 2)
            )

        # =====================================================
        # INNER ORBIT
        # =====================================================

        inner_r = 100 * scale

        pen = QPen(
            QColor(
                0,
                230,
                255,
                190
            )
        )

        pen.setWidthF(
            2
        )

        painter.setPen(
            pen
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawEllipse(
            int(cx - inner_r),
            int(cy - inner_r),
            int(inner_r * 2),
            int(inner_r * 2)
        )

        # =====================================================
        # INNER ROTATING ARC
        # =====================================================

        painter.setPen(
            QPen(
                QColor(
                    100,
                    250,
                    255,
                    240
                ),
                2
            )
        )

        painter.drawArc(
            int(cx - inner_r),
            int(cy - inner_r),
            int(inner_r * 2),
            int(inner_r * 2),
            int(self.rotation3 * 16),
            110 * 16
        )

        painter.drawArc(
            int(cx - inner_r),
            int(cy - inner_r),
            int(inner_r * 2),
            int(inner_r * 2),
            int((self.rotation3 + 180) * 16),
            70 * 16
        )

        # =====================================================
        # CORE OUTER GLOW
        # =====================================================

        pulse_value = (
            math.sin(self.pulse)
            + 1
        ) / 2

        core_radius = (
            78
            + pulse_value * 5
        ) * scale

        self.draw_glow(
            painter,
            cx,
            cy,
            core_radius * 2.2,
            85
        )

        # =====================================================
        # CORE SPHERE
        # =====================================================

        sphere_gradient = QRadialGradient(
            cx - 15 * scale,
            cy - 15 * scale,
            core_radius
        )

        sphere_gradient.setColorAt(
            0.0,
            QColor(
                255,
                255,
                255,
                255
            )
        )

        sphere_gradient.setColorAt(
            0.12,
            QColor(
                170,
                255,
                255,
                255
            )
        )

        sphere_gradient.setColorAt(
            0.35,
            QColor(
                0,
                235,
                255,
                230
            )
        )

        sphere_gradient.setColorAt(
            0.65,
            QColor(
                0,
                120,
                220,
                120
            )
        )

        sphere_gradient.setColorAt(
            1.0,
            QColor(
                0,
                50,
                110,
                0
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QBrush(
                sphere_gradient
            )
        )

        painter.drawEllipse(
            int(cx - core_radius),
            int(cy - core_radius),
            int(core_radius * 2),
            int(core_radius * 2)
        )

        # =====================================================
        # CORE RINGS
        # =====================================================

        for radius, alpha, width in [

            (70, 210, 2),

            (58, 160, 1),

            (46, 100, 1)

        ]:

            r = radius * scale

            painter.setBrush(
                Qt.NoBrush
            )

            painter.setPen(
                QPen(
                    QColor(
                        0,
                        240,
                        255,
                        alpha
                    ),
                    width
                )
            )

            painter.drawEllipse(
                int(cx - r),
                int(cy - r),
                int(r * 2),
                int(r * 2)
            )

        # =====================================================
        # CORE ROTATING LIGHT
        # =====================================================

        light_gradient = QConicalGradient(
            cx,
            cy,
            self.rotation
        )

        light_gradient.setColorAt(
            0.0,
            QColor(
                255,
                255,
                255,
                220
            )
        )

        light_gradient.setColorAt(
            0.15,
            QColor(
                0,
                240,
                255,
                180
            )
        )

        light_gradient.setColorAt(
            0.5,
            QColor(
                0,
                120,
                255,
                30
            )
        )

        light_gradient.setColorAt(
            1.0,
            QColor(
                255,
                255,
                255,
                220
            )
        )

        painter.setBrush(
            QBrush(
                light_gradient
            )
        )

        painter.drawEllipse(
            int(cx - 40 * scale),
            int(cy - 40 * scale),
            int(80 * scale),
            int(80 * scale)
        )

        # =====================================================
        # CENTER STAR
        # =====================================================

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                255,
                255,
                255,
                250
            )
        )

        star_size = (
            18 * scale
        )

        points = []

        for i in range(8):

            angle = (
                -math.pi / 2
                + i * math.pi / 4
            )

            radius = (
                star_size
                if i % 2 == 0
                else star_size * 0.25
            )

            points.append(
                (
                    cx
                    + math.cos(angle)
                    * radius,

                    cy
                    + math.sin(angle)
                    * radius
                )
            )

        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF

        polygon = QPolygonF(
            [
                QPointF(x, y)
                for x, y in points
            ]
        )

        painter.drawPolygon(
            polygon
        )

        # =====================================================
        # STATUS
        # =====================================================

        states = {

            "idle": (
                "READY",
                "I'm here and ready to assist you."
            ),

            "listening": (
                "LISTENING",
                "I'm listening..."
            ),

            "thinking": (
                "THINKING",
                "Processing your request..."
            ),

            "speaking": (
                "SPEAKING",
                "LUNA is speaking..."
            )
        }

        state_text, description = states.get(
            self.state,
            states["idle"]
        )

        status_y = (
            cy
            + 275 * scale
        )

        painter.setPen(
            QColor(
                0,
                235,
                255,
                230
            )
        )

        font = painter.font()

        font.setPixelSize(
            14
        )

        font.setBold(
            True
        )

        painter.setFont(
            font
        )

        painter.drawText(
            0,
            int(status_y),
            width,
            25,
            Qt.AlignCenter,
            "●  " + state_text
        )

        # =====================================================
        # DESCRIPTION
        # =====================================================

        painter.setPen(
            QColor(
                90,
                120,
                135,
                220
            )
        )

        font = painter.font()

        font.setPixelSize(
            12
        )

        font.setBold(
            False
        )

        painter.setFont(
            font
        )

        painter.drawText(
            0,
            int(status_y + 23),
            width,
            25,
            Qt.AlignCenter,
            description
        )

        painter.end()


# ============================================================
# ============================================================
#
#   🌙 LUNA CORE PRO — VISUAL EXTENSIONS (APPEND ONLY)
#
#   The original LunaCore above is 100% unchanged.
#   LunaCorePro subclasses it and paints EXTRA layers on top:
#
#     • State color themes (9 states, each with its own hue)
#     • 5 new states: processing, success, error, alert, sleep
#     • Audio-reactive ring (feed mic/TTS loudness into it)
#     • Task progress ring (tie it to ActionExecutor steps)
#     • Particle bursts + expanding ripples on state change
#     • Click the core → signal + callback (wake/stop)
#     • Hover glow + pointing-hand cursor over the core
#     • Toast messages ("Opening YouTube...") under the core
#     • Demo mode that cycles all states for previews
#
#   Zero new dependencies. Pure PySide6.
#
# ============================================================
# ============================================================

import time

from PySide6.QtCore import Signal, QRectF, QPointF


class LunaCorePro(LunaCore):

    # =========================================================
    # SIGNALS
    # =========================================================

    core_clicked = Signal()

    # =========================================================
    # STATE THEMES  (color + glow strength per state)
    # =========================================================

    STATE_THEMES = {
        "idle":       {"color": (0, 235, 255),   "strength": 0.55},
        "listening":  {"color": (70, 255, 170),  "strength": 0.80},
        "thinking":   {"color": (185, 125, 255), "strength": 0.75},
        "speaking":   {"color": (90, 180, 255),  "strength": 0.80},
        "processing": {"color": (255, 200, 90),  "strength": 0.75},
        "success":    {"color": (90, 255, 150),  "strength": 0.95},
        "error":      {"color": (255, 95, 95),   "strength": 1.00},
        "alert":      {"color": (255, 160, 70),  "strength": 0.95},
        "sleep":      {"color": (110, 130, 150), "strength": 0.25},
    }

    STATE_LABELS = {
        "idle":       ("READY",     "I'm here and ready to assist you."),
        "listening":  ("LISTENING", "I'm listening..."),
        "thinking":   ("THINKING",  "Processing your request..."),
        "speaking":   ("SPEAKING",  "LUNA is speaking..."),
        "processing": ("WORKING",   "Running your task..."),
        "success":    ("DONE",      "Task completed successfully."),
        "error":      ("ERROR",     "Something went wrong. Try again."),
        "alert":      ("ATTENTION", "LUNA needs your attention."),
        "sleep":      ("SLEEPING",  "Click the core to wake LUNA."),
    }

    def __init__(self, parent=None):

        super().__init__(parent)

        # -----------------------------
        # AUDIO REACTIVITY (0.0 - 1.0)
        # -----------------------------

        self.audio_level = 0.0
        self.audio_level_smooth = 0.0

        # -----------------------------
        # TASK PROGRESS (None or 0-1)
        # -----------------------------

        self.progress = None

        # -----------------------------
        # EFFECTS
        # -----------------------------

        self.bursts = []
        self.ripples = []
        self.hover = False

        # -----------------------------
        # TOAST MESSAGE
        # -----------------------------

        self.toast_text = None
        self.toast_start = 0.0
        self.toast_duration = 4.0

        # -----------------------------
        # CLICK HOOK
        # -----------------------------

        self.click_callback = None

        # -----------------------------
        # DEMO MODE
        # -----------------------------

        self.demo_index = 0

        self.demo_states = [
            "idle",
            "listening",
            "thinking",
            "speaking",
            "success",
            "idle",
            "error",
            "idle",
        ]

        self.demo_timer = QTimer(self)

        self.demo_timer.timeout.connect(
            self._demo_tick
        )

        self.setMouseTracking(True)

    # =========================================================
    # STATE (with burst + ripple on change)
    # =========================================================

    def set_state(self, state):

        new_state = str(
            state
        ).lower()

        if new_state != self.state:

            self._spawn_burst(new_state)
            self._spawn_ripple(new_state)

        super().set_state(state)

    # =========================================================
    # PUBLIC API — call these from LUNA's voice loop
    # =========================================================

    def set_audio_level(self, level):

        try:

            level = float(level)

        except (
            TypeError,
            ValueError
        ):

            return

        self.audio_level = max(
            0.0,
            min(1.0, level)
        )

    def set_progress(self, value):

        if value is None:

            self.progress = None
            self.update()

            return

        try:

            value = float(value)

        except (
            TypeError,
            ValueError
        ):

            return

        self.progress = max(
            0.0,
            min(1.0, value)
        )

        self.update()

    def clear_progress(self):

        self.progress = None

        self.update()

    def show_message(
        self,
        text,
        duration=4.0
    ):

        if not text:

            return

        self.toast_text = str(text)

        self.toast_start = (
            time.monotonic()
        )

        self.toast_duration = max(
            1.0,
            float(duration)
        )

        self.update()

    def set_click_callback(self, callback):

        self.click_callback = callback

    def start_demo(self):

        self.demo_index = 0

        self.demo_timer.start(2200)

    def stop_demo(self):

        self.demo_timer.stop()

        self.set_state("idle")

    def _demo_tick(self):

        state = self.demo_states[
            self.demo_index
            % len(self.demo_states)
        ]

        self.demo_index += 1

        self.set_state(state)

    # =========================================================
    # EFFECT SPAWNERS
    # =========================================================

    def _spawn_burst(self, state):

        theme = self.STATE_THEMES.get(
            state,
            self.STATE_THEMES["idle"]
        )

        cr, cg, cb = theme["color"]

        for _ in range(26):

            self.bursts.append({
                "angle": random.uniform(0, 360),
                "start": random.uniform(60, 90),
                "travel": random.uniform(120, 210),
                "size": random.uniform(1.2, 3.2),
                "life": 0.0,
                "max_life": random.uniform(0.6, 1.1),
                "r": cr,
                "g": cg,
                "b": cb,
            })

    def _spawn_ripple(self, state):

        theme = self.STATE_THEMES.get(
            state,
            self.STATE_THEMES["idle"]
        )

        cr, cg, cb = theme["color"]

        self.ripples.append({
            "start": 95.0,
            "travel": 150.0,
            "life": 0.0,
            "max_life": 1.1,
            "alpha": 150,
            "r": cr,
            "g": cg,
            "b": cb,
        })

    # =========================================================
    # ANIMATION (base + effect physics)
    # =========================================================

    def animate(self):

        super().animate()

        self.audio_level_smooth += (
            self.audio_level
            - self.audio_level_smooth
        ) * 0.25

        for particle in self.bursts:

            particle["life"] += 0.016

        self.bursts = [
            p
            for p in self.bursts
            if p["life"] < p["max_life"]
        ]

        for ripple in self.ripples:

            ripple["life"] += 0.016

        self.ripples = [
            r
            for r in self.ripples
            if r["life"] < r["max_life"]
        ]

    # =========================================================
    # MOUSE — click + hover on the core
    # =========================================================

    def _hit_core(self, x, y):

        cx = self.width() / 2
        cy = self.height() / 2 - 10

        scale = min(
            self.width(),
            self.height()
        ) / 620

        return (
            math.hypot(x - cx, y - cy)
            <= 95 * scale
        )

    def mousePressEvent(self, event):

        pos = event.position()

        if self._hit_core(
            pos.x(),
            pos.y()
        ):

            self._spawn_burst(
                self.state
            )

            self.core_clicked.emit()

            if self.click_callback:

                try:

                    self.click_callback()

                except Exception as error:

                    print(
                        f"[LUNA CORE] Click callback error: {error}"
                    )

            event.accept()

            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        pos = event.position()

        over = self._hit_core(
            pos.x(),
            pos.y()
        )

        if over != self.hover:

            self.hover = over

            self.setCursor(
                Qt.PointingHandCursor
                if over
                else Qt.ArrowCursor
            )

            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):

        if self.hover:

            self.hover = False

            self.setCursor(
                Qt.ArrowCursor
            )

            self.update()

        super().leaveEvent(event)

    # =========================================================
    # PAINT — base visual + extra layers
    # =========================================================

    def paintEvent(self, event):

        # Original LUNA visual
        # (draws everything, then ends its painter)

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        width = self.width()
        height = self.height()

        cx = width / 2
        cy = height / 2 - 10

        scale = min(
            width,
            height
        ) / 620

        theme = self.STATE_THEMES.get(
            self.state,
            self.STATE_THEMES["idle"]
        )

        cr, cg, cb = theme["color"]

        strength = theme["strength"]

        self._draw_energy_rays(
            painter, cx, cy, scale, cr, cg, cb
        )

        self._draw_mood_ring(
            painter, cx, cy, scale, cr, cg, cb, strength
        )

        self._draw_hover_ring(
            painter, cx, cy, scale, cr, cg, cb
        )

        self._draw_audio_ring(
            painter, cx, cy, scale, cr, cg, cb
        )

        self._draw_progress(
            painter, cx, cy, scale, cr, cg, cb
        )

        self._draw_ripples(
            painter, cx, cy, scale
        )

        self._draw_bursts(
            painter, cx, cy, scale
        )

        status_y = (
            cy
            + 275 * scale
        )

        self._draw_status(
            painter, width, status_y, cr, cg, cb
        )

        self._draw_toast(
            painter, width, status_y
        )

        painter.end()

    # =========================================================
    # LAYER: ROTATING ENERGY RAYS
    # =========================================================

    def _draw_energy_rays(
        self,
        painter,
        cx,
        cy,
        scale,
        cr,
        cg,
        cb
    ):

        painter.setBrush(
            Qt.NoBrush
        )

        for index in range(14):

            angle = math.radians(
                self.rotation3 * 0.7
                + index * (360 / 14)
            )

            inner = 150 * scale

            outer = inner + (
                16
                + 12
                * math.sin(
                    self.pulse * 1.5
                    + index
                )
            ) * scale

            alpha = int(
                12
                + 12
                * max(
                    0.0,
                    math.sin(
                        self.pulse
                        + index * 0.9
                    )
                )
            )

            pen = QPen(
                QColor(cr, cg, cb, alpha)
            )

            pen.setWidthF(1.2)

            painter.setPen(pen)

            painter.drawLine(
                QPointF(
                    cx + math.cos(angle) * inner,
                    cy + math.sin(angle) * inner,
                ),
                QPointF(
                    cx + math.cos(angle) * outer,
                    cy + math.sin(angle) * outer,
                ),
            )

    # =========================================================
    # LAYER: STATE MOOD RING
    # =========================================================

    def _draw_mood_ring(
        self,
        painter,
        cx,
        cy,
        scale,
        cr,
        cg,
        cb,
        strength
    ):

        radius = 132 * scale

        breathe = (
            0.75
            + 0.25
            * math.sin(self.pulse * 1.6)
        )

        alpha = int(
            80 * strength * breathe
        )

        gradient = QRadialGradient(
            cx,
            cy,
            radius
        )

        gradient.setColorAt(
            0.00,
            QColor(cr, cg, cb, 0)
        )

        gradient.setColorAt(
            0.55,
            QColor(cr, cg, cb, 0)
        )

        gradient.setColorAt(
            0.72,
            QColor(cr, cg, cb, alpha)
        )

        gradient.setColorAt(
            0.86,
            QColor(
                cr, cg, cb,
                int(alpha * 0.35)
            )
        )

        gradient.setColorAt(
            1.00,
            QColor(cr, cg, cb, 0)
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QBrush(gradient)
        )

        painter.drawEllipse(
            int(cx - radius),
            int(cy - radius),
            int(radius * 2),
            int(radius * 2)
        )

    # =========================================================
    # LAYER: HOVER RING
    # =========================================================

    def _draw_hover_ring(
        self,
        painter,
        cx,
        cy,
        scale,
        cr,
        cg,
        cb
    ):

        if not self.hover:

            return

        r = 95 * scale

        pen = QPen(
            QColor(cr, cg, cb, 70)
        )

        pen.setWidthF(1.4)

        painter.setPen(pen)

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawEllipse(
            int(cx - r),
            int(cy - r),
            int(r * 2),
            int(r * 2)
        )

    # =========================================================
    # LAYER: AUDIO-REACTIVE RING (listening / speaking)
    # =========================================================

    def _draw_audio_ring(
        self,
        painter,
        cx,
        cy,
        scale,
        cr,
        cg,
        cb
    ):

        if self.state not in (
            "listening",
            "speaking"
        ):

            return

        bars = 64

        base_r = 118 * scale

        max_len = 30 * scale

        level = self.audio_level_smooth

        spin = self.rotation * 0.4

        for index in range(bars):

            angle = math.radians(
                (index / bars) * 360
                + spin
            )

            wave = abs(
                math.sin(
                    self.pulse * 2.2
                    + index * 0.55
                )
                * math.cos(
                    self.pulse * 1.3
                    + index * 0.21
                )
            )

            amplitude = max(
                level,
                wave * 0.55
            )

            length = max_len * (
                0.12
                + 0.88 * amplitude
            )

            x1 = (
                cx
                + math.cos(angle)
                * base_r
            )

            y1 = (
                cy
                + math.sin(angle)
                * base_r
            )

            x2 = (
                cx
                + math.cos(angle)
                * (base_r + length)
            )

            y2 = (
                cy
                + math.sin(angle)
                * (base_r + length)
            )

            pen = QPen(
                QColor(
                    cr,
                    cg,
                    cb,
                    int(110 + 120 * amplitude)
                )
            )

            pen.setWidthF(2.2)

            pen.setCapStyle(
                Qt.RoundCap
            )

            painter.setPen(pen)

            painter.drawLine(
                QPointF(x1, y1),
                QPointF(x2, y2)
            )

    # =========================================================
    # LAYER: TASK PROGRESS RING
    # =========================================================

    def _draw_progress(
        self,
        painter,
        cx,
        cy,
        scale,
        cr,
        cg,
        cb
    ):

        if self.progress is None:

            return

        value = max(
            0.0,
            min(1.0, self.progress)
        )

        r = 248 * scale

        track = QPen(
            QColor(0, 210, 245, 36)
        )

        track.setWidthF(3.5)

        track.setCapStyle(
            Qt.RoundCap
        )

        painter.setPen(track)

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawArc(
            int(cx - r),
            int(cy - r),
            int(r * 2),
            int(r * 2),
            0,
            360 * 16
        )

        pen = QPen(
            QColor(cr, cg, cb, 235)
        )

        pen.setWidthF(4.5)

        pen.setCapStyle(
            Qt.RoundCap
        )

        painter.setPen(pen)

        span = int(
            value * 360 * 16
        )

        painter.drawArc(
            int(cx - r),
            int(cy - r),
            int(r * 2),
            int(r * 2),
            90 * 16,
            -span
        )

    # =========================================================
    # LAYER: EXPANDING RIPPLES
    # =========================================================

    def _draw_ripples(
        self,
        painter,
        cx,
        cy,
        scale
    ):

        painter.setBrush(
            Qt.NoBrush
        )

        for ripple in self.ripples:

            t = (
                ripple["life"]
                / ripple["max_life"]
            )

            radius = (
                ripple["start"]
                + ripple["travel"] * t
            ) * scale

            alpha = int(
                ripple["alpha"]
                * (1.0 - t)
            )

            pen = QPen(
                QColor(
                    ripple["r"],
                    ripple["g"],
                    ripple["b"],
                    alpha
                )
            )

            pen.setWidthF(2.0)

            painter.setPen(pen)

            painter.drawEllipse(
                int(cx - radius),
                int(cy - radius),
                int(radius * 2),
                int(radius * 2)
            )

    # =========================================================
    # LAYER: PARTICLE BURSTS
    # =========================================================

    def _draw_bursts(
        self,
        painter,
        cx,
        cy,
        scale
    ):

        painter.setPen(
            Qt.NoPen
        )

        for particle in self.bursts:

            t = (
                particle["life"]
                / particle["max_life"]
            )

            ease = (
                1.0
                - (1.0 - t) ** 2
            )

            distance = (
                particle["start"]
                + particle["travel"] * ease
            ) * scale

            angle = math.radians(
                particle["angle"]
            )

            x = (
                cx
                + math.cos(angle)
                * distance
            )

            y = (
                cy
                + math.sin(angle)
                * distance
            )

            size = (
                particle["size"]
                * scale
                * (1.0 - t * 0.5)
            )

            painter.setBrush(
                QColor(
                    particle["r"],
                    particle["g"],
                    particle["b"],
                    int(220 * (1.0 - t))
                )
            )

            painter.drawEllipse(
                int(x - size),
                int(y - size),
                int(size * 2),
                int(size * 2)
            )

    # =========================================================
    # LAYER: THEMED STATUS TEXT (covers base text)
    # =========================================================

    def _draw_status(
        self,
        painter,
        width,
        status_y,
        cr,
        cg,
        cb
    ):

        label, description = (
            self.STATE_LABELS.get(
                self.state,
                self.STATE_LABELS["idle"]
            )
        )

        painter.fillRect(
            0,
            int(status_y - 6),
            width,
            54,
            QColor("#02070D")
        )

        blink = 1.0

        if self.state in (
            "listening",
            "processing",
            "error",
            "alert"
        ):

            blink = (
                0.55
                + 0.45
                * abs(math.sin(self.pulse * 3))
            )

        font = painter.font()

        font.setPixelSize(14)

        font.setBold(True)

        painter.setFont(font)

        painter.setPen(
            QColor(
                cr,
                cg,
                cb,
                int(235 * blink)
            )
        )

        painter.drawText(
            0,
            int(status_y),
            width,
            25,
            Qt.AlignCenter,
            "●  " + label
        )

        font.setPixelSize(12)

        font.setBold(False)

        painter.setFont(font)

        painter.setPen(
            QColor(140, 165, 180, 220)
        )

        painter.drawText(
            0,
            int(status_y + 23),
            width,
            25,
            Qt.AlignCenter,
            description
        )

    # =========================================================
    # LAYER: TOAST MESSAGE
    # =========================================================

    def _draw_toast(
        self,
        painter,
        width,
        status_y
    ):

        if not self.toast_text:

            return

        elapsed = (
            time.monotonic()
            - self.toast_start
        )

        remaining = (
            self.toast_duration
            - elapsed
        )

        if remaining <= 0:

            self.toast_text = None

            return

        fade = min(
            1.0,
            elapsed / 0.25,
            remaining / 0.6
        )

        font = painter.font()

        font.setPixelSize(13)

        font.setBold(False)

        painter.setFont(font)

        metrics = painter.fontMetrics()

        text_width = (
            metrics.horizontalAdvance(
                self.toast_text
            )
        )

        bubble_w = text_width + 36

        bubble_h = 30

        bubble_x = (
            (width - bubble_w) / 2
        )

        bubble_y = status_y + 56

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                0,
                45,
                70,
                int(130 * fade)
            )
        )

        painter.drawRoundedRect(
            QRectF(
                bubble_x,
                bubble_y,
                bubble_w,
                bubble_h
            ),
            10,
            10
        )

        painter.setPen(
            QColor(
                180,
                245,
                255,
                int(235 * fade)
            )
        )

        painter.drawText(
            QRectF(
                bubble_x,
                bubble_y,
                bubble_w,
                bubble_h
            ),
            Qt.AlignCenter,
            self.toast_text
        )


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports LunaCore from this file now gets the
# extended version automatically (same API, more features).
# Delete the next line to keep using the original visual.
# ------------------------------------------------------------

LunaCore = LunaCorePro


# ============================================================
# QUICK TEST (uncomment to preview all states)
# ============================================================
#
# if __name__ == "__main__":
#
#     import sys
#     from PySide6.QtWidgets import QApplication
#
#     app = QApplication(sys.argv)
#
#     core = LunaCore()
#     core.show()
#     core.start_demo()
#
#     sys.exit(app.exec())