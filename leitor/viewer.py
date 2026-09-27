from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QColor, QBrush, QPen, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene


class PDFView(QGraphicsView):
    chosen = Signal(int)

    def __init__(self):
        super().__init__()
        self.canvas = QGraphicsScene(self)
        self.setScene(self.canvas)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor("#e5e8e6"))
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.regions, self.highlights = [], []
        self.zoom = 1.0
        self.press = None
        self.setMinimumWidth(400)

    def show_page(self, png, scale, regions):
        self.canvas.clear()
        self.highlights = []
        pix = QPixmap()
        if not pix.loadFromData(png, "PNG"):
            raise ValueError("Não foi possível desenhar a página.")
        item = self.canvas.addPixmap(pix)
        item.setScale(1 / scale)
        self.canvas.setSceneRect(item.sceneBoundingRect())
        self.regions = regions

    def set_zoom(self, zoom):
        self.zoom = zoom
        self.resetTransform()
        self.scale(zoom, zoom)

    def highlight(self, index, playing=False, follow=False):
        for item in self.highlights:
            self.canvas.removeItem(item)
        self.highlights = []
        first = None
        for i, box in self.regions:
            if i != index:
                continue
            rect = QRectF(box[0], box[1], box[2] - box[0], box[3] - box[1])
            item = self.canvas.addRect(rect, QPen(Qt.PenStyle.NoPen),
                QBrush(QColor(45, 170, 105, 85) if playing else QColor(245, 180, 40, 90)))
            item.setZValue(2)
            self.highlights.append(item)
            if first is None:
                first = rect
        if follow and first:
            self.ensureVisible(first, 35, 60)

    def clear_page(self):
        self.canvas.clear()
        self.regions, self.highlights = [], []

    def mousePressEvent(self, event):
        self.press = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.press is not None and (event.position() - self.press).manhattanLength() < 5:
            point = self.mapToScene(event.position().toPoint())
            best = None
            for index, box in self.regions:
                dx = max(box[0] - point.x(), 0, point.x() - box[2])
                dy = max(box[1] - point.y(), 0, point.y() - box[3])
                distance = dx * dx + dy * dy
                if distance <= 100 and (best is None or distance < best[0]):
                    best = (distance, index)
            if best:
                self.chosen.emit(best[1])
        self.press = None
        super().mouseReleaseEvent(event)
