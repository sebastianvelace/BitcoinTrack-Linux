import sys
from typing import Optional, Tuple

import requests
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
UPDATE_OK_MS = 60_000
# Sin red: reintento indefinido cada 5s (no usamos time.sleep para no congelar la GUI)
OFFLINE_RETRY_MS = 5_000


class BTCTicker(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initUI()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ticker)

        app = QApplication.instance()
        if app:
            for scr in app.screens():
                scr.geometryChanged.connect(self.adjust_position)
                scr.availableGeometryChanged.connect(self.adjust_position)

        self.update_ticker()

    def initUI(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Tipo de ventana X11: panel/dock persistente (en Wayland puro suele ignorarse)
        self.setAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeDock)

        # Saltarse la barra de tareas
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout()
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(0, 0, 0, 230);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QLabel { color: white; background: transparent; border: none; }
        """
        )

        self.price_label = QLabel("Cargando...")
        self.price_label.setFont(QFont("Inter", 15, QFont.Weight.Bold))

        self.change_label = QLabel("0.00% (24h)")
        self.change_label.setFont(QFont("Inter", 9))

        # Sombra del widget (legibilidad sobre fondos claros)
        widget_shadow = QGraphicsDropShadowEffect(self)
        widget_shadow.setBlurRadius(15)
        widget_shadow.setOffset(0, 0)
        widget_shadow.setColor(QColor(0, 0, 0, int(255 * 0.5)))
        self.setGraphicsEffect(widget_shadow)

        # Contorno sutil en el texto blanco
        for lbl in (self.price_label, self.change_label):
            text_shadow = QGraphicsDropShadowEffect(lbl)
            text_shadow.setBlurRadius(3)
            text_shadow.setOffset(0, 0)
            text_shadow.setColor(QColor(0, 0, 0, 220))
            lbl.setGraphicsEffect(text_shadow)

        layout.addWidget(self.price_label)
        layout.addWidget(self.change_label)
        self.setLayout(layout)

        # Fijar tamaño ANTES de cualquier cálculo de posición (coords precisas)
        self.setFixedSize(160, 70)

    def adjust_position(self) -> None:
        # Área de trabajo (sin dock/panel): QScreen.availableGeometry()
        app = QApplication.instance()
        if app is None:
            return
        primary = app.primaryScreen()
        if primary is None:
            return
        screen = primary.availableGeometry()

        x = screen.left() + 20
        y = screen.top() + screen.height() - self.height() - 20

        self.setGeometry(x, y, self.width(), self.height())

    def fetch_btc_data(self) -> Optional[Tuple[float, float]]:
        try:
            resp = requests.get(BINANCE_URL, timeout=6)
            resp.raise_for_status()
            payload = resp.json()
            last_price = float(payload["lastPrice"])
            change_pct = float(payload["priceChangePercent"])
            return last_price, change_pct
        except Exception:
            return None

    def update_ticker(self) -> None:
        data = self.fetch_btc_data()

        if data is None:
            self.price_label.setText("Sin conexion")
            self.change_label.setText("Reintentando en 5s")
            self.change_label.setStyleSheet("color: #9E9E9E; background: transparent; border: none;")
            self._set_timer_interval(OFFLINE_RETRY_MS)
            self.adjust_position()
            return

        last_price, change_pct = data
        self.price_label.setText(f"${last_price:,.2f}")

        sign = "+" if change_pct >= 0 else ""
        self.change_label.setText(f"{sign}{change_pct:.2f}% (24h)")
        color = "#22C55E" if change_pct >= 0 else "#EF4444"
        self.change_label.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )

        self._set_timer_interval(UPDATE_OK_MS)
        self.adjust_position()

    def _set_timer_interval(self, ms: int) -> None:
        if self.timer.interval() != ms or not self.timer.isActive():
            self.timer.start(ms)

    def contextMenuEvent(self, event: QEvent) -> None:
        menu = QMenu(self)
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        menu.exec(QCursor.pos())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Wayland: retrasar el move para que el compositor ya haya mapeado la ventana
        QTimer.singleShot(200, self.adjust_position)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    ticker = BTCTicker()
    ticker.show()

    sys.exit(app.exec())
