from PyQt6.QtGui import QPen, QColor

class Connection:
    def __init__(self, start_block, end_block):
        self.start_block = start_block
        self.end_block = end_block

    def draw(self, painter):
        pen = QPen(QColor(50, 50, 50), 3)
        painter.setPen(pen)
        painter.drawLine(self.start_block.center(), self.end_block.center())