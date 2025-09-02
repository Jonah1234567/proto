# io_mapper_dialog.py (self-contained)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGridLayout,
    QComboBox, QWidget, QScrollArea, QSizePolicy, QMessageBox, QFrame, QLineEdit,
    QStackedWidget, QSlider, QTableWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsPathItem, QMenu
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPen, QColor, QCursor
import math


class IOMapperDialog(QDialog):
    """
    Two-mode IO mapper:
      - MENU mode: dropdowns (classic)
      - WIRE mode: mini bipartite canvas (left=upstream outputs, right=this block's inputs)
    Persists to block.input_mappings in the same schema you already use.
    """
    MODE_WIRE = 0
    MODE_MENU = 1

    def __init__(self, block, parent=None):
        super().__init__(parent)
        self.block = block
        self.setWindowTitle(f"IO Mapper – {getattr(block, 'name', 'Block')}")
        self.setMinimumSize(940, 720)

        # Snapshot upstream outputs and this block's inputs
        self._inputs = self._get_inputs(block)              # list[str]
        self._upstreams = self._get_upstream_outputs(block) # list of (blk_name, blk_id, out_name)

        # UI state
        self._rows = {}  # MENU mode: input_name -> (label, combo)
        self._wires = [] # WIRE mode: list of Wire objects

        main = QVBoxLayout(self)

        # --- Header with mode slider ---
        head = QHBoxLayout()
        title = QLabel(f"<b>{getattr(block, 'name', 'Block')}</b> • {len(self._inputs)} inputs • {len(self._upstreams)} upstream outputs")
        title.setProperty("class", "h1")
        subtitle = QLabel("Configure connections via wiring (left) or menus (right).")
        subtitle.setProperty("class", "h2")
        head.addWidget(title, 1)
        head.addWidget(subtitle, 0)


        head.addWidget(QLabel("Wire"))
        self.mode_slider = QSlider(Qt.Orientation.Horizontal)
        self.mode_slider.setMinimum(0); self.mode_slider.setMaximum(1); self.mode_slider.setValue(self.MODE_MENU)  # start in MENU
        self.mode_slider.setFixedWidth(100)
        head.addWidget(self.mode_slider)
        head.addWidget(QLabel("Menu"))
        main.addLayout(head)

        # --- Filter + buttons ---
        toolbar = QHBoxLayout()
        self.filter_edit = QLineEdit(placeholderText="Filter inputs or sources…")
        toolbar.addWidget(self.filter_edit, 1)

        self.btn_automap = QPushButton("Auto-map by name")
        self.btn_clear = QPushButton("Clear all")
        toolbar.addWidget(self.btn_automap)
        toolbar.addWidget(self.btn_clear)
        main.addLayout(toolbar)

        main.addWidget(self._divider())

        # --- Stacked views (WIRE / MENU) ---
        self.stack = QStackedWidget()
        self.menu_view = self._build_menu_view()
        self.wire_view = self._build_wire_view()
        self.stack.addWidget(self.wire_view)
        self.stack.addWidget(self.menu_view)
        self.stack.setCurrentIndex(self.MODE_MENU)
        main.addWidget(self.stack, 1)

        main.addWidget(self._divider())

        # --- Footer ---
        footer = QHBoxLayout()
        footer.addStretch()
        self.btn_save = QPushButton("Save")
        self.btn_close = QPushButton("Close")
        self.btn_save.setDefault(True)
        footer.addWidget(self.btn_save)
        footer.addWidget(self.btn_close)
        main.addLayout(footer)

        # --- Style ---
        self.setStyleSheet(self.styleSheet() + """
        /* Modern scrollbars for both QGraphicsView and QScrollArea */
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #C8CCD4;
            min-height: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover { background: #B0B6C0; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

        QScrollBar:horizontal {
            background: transparent;
            height: 10px;
            margin: 0;
        }
        QScrollBar::handle:horizontal {
            background: #C8CCD4;
            min-width: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover { background: #B0B6C0; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)

        # --- Wire up ---
        self.mode_slider.valueChanged.connect(self._on_mode_change)
        self.btn_close.clicked.connect(self.accept)
        self.btn_save.clicked.connect(self._save_and_close)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_automap.clicked.connect(self._automap_by_name)
        self.filter_edit.textChanged.connect(self._apply_filter)

        # Load saved mappings (applies to both views)
        self._load_saved_into_views()

    # ======================
    # Helpers & data access
    # ======================

    def _get_inputs(self, block):
        ins = getattr(block, "inputs", None)
        if hasattr(ins, "to_dict"):
            d = ins.to_dict() or {}
            return list(d.keys())
        if isinstance(ins, dict):
            return list(ins.keys())
        # fallback: check input_mappings keys
        im = getattr(block, "input_mappings", {})
        if isinstance(im, dict):
            return list(im.keys())
        return []

    def _get_upstream_outputs(self, block):
        """Return list of (blk_name, blk_id, output_name)."""
        seen = set()
        upstreams = []
        for conn in getattr(block, "incoming_connections", []):
            if conn.end_block is block and id(conn.start_block) not in seen:
                seen.add(id(conn.start_block))
                ub = conn.start_block
                outs = getattr(ub, "outputs", None)
                od = outs.to_dict() if hasattr(outs, "to_dict") else (outs or {})
                for out_name in (od.keys() if isinstance(od, dict) else []):
                    upstreams.append((getattr(ub, "name", "Block"), getattr(ub, "id", None), out_name))
        return upstreams

    def _divider(self):
        d = QFrame()
        d.setObjectName("Divider")
        d.setFrameShape(QFrame.Shape.HLine)
        d.setFixedHeight(1)
        d.setStyleSheet("background:#E7E7E7;")
        return d


    # ======================
    # MENU mode view
    # ======================

    def _build_menu_view(self):
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(12)

        # Card
        card = QWidget()
        card.setObjectName("MenuCard")                    # << scope by id
        card.setStyleSheet("""
            #MenuCard {
                background: #FAFAFA;
                border: 1px solid #E5E5E5;
                border-radius: 12px;
            }
        """)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16,16,16,16)
        card_lay.setSpacing(12)

        header = QLabel("Inputs ↔ Sources")
        header.setProperty("class", "h1")
        card_lay.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        body = QWidget()
        grid = QGridLayout(body)
       # inside _build_menu_view(), after creating `grid`
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 0)   # labels
        grid.setColumnStretch(1, 1)   # combos

        # header row
        grid.addWidget(QLabel("<b>Input</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Source</b>"), 0, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 140)


        self._rows.clear()
        row = 1
        if not self._inputs:
            empty = QLabel("⚠️ This block has no defined inputs.")
            empty.setStyleSheet("color:#666;")
            grid.addWidget(empty, row, 0, 1, 2)
        else:
           for input_name in self._inputs:
            lbl = QLabel(input_name)
            lbl.setMinimumWidth(140)
            lbl.setMaximumWidth(200)
            lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            combo = QComboBox()
            combo.addItem("— Not Connected —", userData=None)
            for (blk_name, blk_id, out_name) in self._upstreams:
                combo.addItem(f"{blk_name}.{out_name}", userData=(blk_id, out_name))

            # compact sizing
            combo.setFixedHeight(28)
            combo.setMinimumWidth(220)
            combo.setMaximumWidth(320)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(14)
            # shrink padding even if global CSS is generous
            combo.setStyleSheet("QComboBox{min-height:24px;padding:2px 6px;}")

            grid.addWidget(lbl, row, 0)
            grid.addWidget(combo, row, 1)
            self._rows[input_name] = (lbl, combo)
            row += 1


        scroll.setWidget(body)
        card_lay.addWidget(scroll)
        layout.addWidget(card)
        return wrap

    def _apply_filter(self):
        q = self.filter_edit.text().strip().lower()
        # MENU filter
        for name, (lbl, combo) in self._rows.items():
            show = (q in name.lower()) or any(q in combo.itemText(i).lower() for i in range(combo.count()))
            lbl.setVisible(show)
            combo.setVisible(show)
        # WIRE filter: just relayout to hide unmatched nodes
        if hasattr(self, "_wire_scene"):
            self._populate_wire_scene(filter_text=q)

    def _clear_all(self):
        # MENU
        for _, combo in self._rows.values():
            combo.setCurrentIndex(0)
        # WIRE
        self._delete_all_wires()

    def _automap_by_name(self):
        # MENU
        for input_name, (_, combo) in self._rows.items():
            tgt = input_name.lower()
            best = 0
            for i in range(1, combo.count()):
                txt = combo.itemText(i).lower()
                if "." in txt and txt.split(".")[-1] == tgt:
                    best = i; break
            combo.setCurrentIndex(best)
        # WIRE
        self._delete_all_wires()
        # build wires to first matching output with same name
        for input_name in self._inputs:
            for (blk_name, blk_id, out_name) in self._upstreams:
                if out_name.lower() == input_name.lower():
                    self._add_wire_by_ids(input_name, blk_id, out_name)
                    break

    # ======================
    # WIRE mode view
    # ======================

    class _PortCircle(QGraphicsEllipseItem):
        def __init__(self, x, y, r, label, role, payload):
            super().__init__(QRectF(x - r, y - r, 2*r, 2*r))
            self.role = role
            self.payload = payload
            self.label_text = label
            self.r = r
            self.setAcceptHoverEvents(True)
            self.setZValue(3)

            # Strong outline + light fill
            self.normal_pen = QPen(QColor("#4A5568"), 1.6)
            self.hover_pen  = QPen(QColor("#111111"), 2.2)
            fill = QColor("#EAF2FF") if role == "out" else QColor("#F4F4F4")
            self.setBrush(fill)
            self.setPen(self.normal_pen)

        def hoverEnterEvent(self, _):
            self.setPen(self.hover_pen)

        def hoverLeaveEvent(self, _):
            self.setPen(self.normal_pen)

    class _Wire(QGraphicsPathItem):
        def __init__(self, src_port, dst_port):
            super().__init__()
            self.src_port = src_port
            self.dst_port = dst_port
            self.setZValue(2)
            pen = QPen(QColor("#1F2937"), 2.4)  # darker, a bit thicker
            self.setPen(pen)
            self._update_path()

        def _update_path(self):
            s = self._center(self.src_port)
            d = self._center(self.dst_port)
            mid_x = (s.x() + d.x()) / 2.0
            path = QPainterPath(s)
            path.cubicTo(QPointF(mid_x, s.y()), QPointF(mid_x, d.y()), d)
            self.setPath(path)

        def _center(self, item):
            rect = item.rect()
            return item.mapToScene(rect.center())

        def contextMenuEvent(self, event):
            menu = QMenu()
            act = menu.addAction("Delete")
            chosen = menu.exec(QCursor.pos())
            if chosen == act:
                self.scene().removeItem(self)


    def _panel(self, x, y, w, h, title):
        """Small helper to draw a card panel in the scene."""
        rect_item = self._wire_scene.addRect(x, y, w, h, QPen(QColor("#E5E5E5"), 1.2), QColor("#FAFAFA"))
        rect_item.setZValue(0)
        t = self._wire_scene.addSimpleText(title)
        t.setBrush(QColor("#111"))
        t.setPos(x + 12, y + 8)
        t.setZValue(1)
        return rect_item

    def _build_wire_view(self):
        wrap = QWidget()
        lay = QVBoxLayout(wrap); lay.setContentsMargins(0,0,0,0)
        self._wire_scene = QGraphicsScene(0, 0, 1200, 900)
        self._wire_view = QGraphicsView(self._wire_scene)
        self._wire_view.setRenderHints(self._wire_view.renderHints() | self._wire_view.renderHints().Antialiasing)
        self._wire_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        lay.addWidget(self._wire_view)
        # state for dragging
        self._dragging_from = None
        self._temp_path = None

        # populate
        self._populate_wire_scene()

        # mouse handling via viewport events
        self._wire_view.viewport().installEventFilter(self)
        return wrap

    def _populate_wire_scene(self, filter_text: str = ""):
        q = filter_text.strip().lower()
        sc = self._wire_scene
        sc.clear()
        self._wires.clear()
        self._port_items_out = []
        self._port_items_in = []

        # Scene/column layout
        margin = 24
        col_w  = 420
        col_h  = 720
        gap_x  = 120  # space between columns
        left_x = margin + 24                 # x of left dots
        right_x = margin + col_w + gap_x + col_w - 24  # x of right dots
        top_y  = margin
        dy     = 48
        dot_r  = 8
        label_gap = 12   # text distance from dot
        lift     = 12    # raise labels above wire level
        header_gap_down = 16  # move headers down closer to first row

        # optional: draw subtle column panels (nice for centering visual)
        def add_panel(x, y, w, h, title):
            rect = sc.addRect(x-12, y-12, w, h, QPen(QColor("#E5E5E5"), 1.2), QColor("#FAFAFA"))
            rect.setZValue(0)
            return rect

        add_panel(margin, top_y, col_w, col_h, "Upstream Outputs")
        add_panel(margin + col_w + gap_x, top_y, col_w, col_h, "Inputs")

        # headers: centered over each column, slightly underlined, moved down a bit
        def add_centered_header(text, center_x, y):
            t = sc.addSimpleText(text)
            f = t.font(); f.setBold(True); f.setUnderline(True)
            t.setFont(f)
            t.setBrush(QColor("#111"))
            br = t.boundingRect()
            pad = 3
            bg = sc.addRect(0, 0, br.width() + pad*2, br.height() + pad*2,
                            QPen(Qt.PenStyle.NoPen), QColor("#FAFAFA"))
            t.setZValue(3.0)
            bg.setZValue(2.5)
            t.setPos(center_x - br.width()/2, y - br.height())     # centered
            bg.setPos(center_x - br.width()/2 - pad, y - br.height() - pad)
            return t, bg

        # filtered lists so we can center vertically
        ups = []
        for (blk_name, blk_id, out_name) in self._upstreams:
            label = f"{blk_name}.{out_name}"
            if not q or q in label.lower():
                ups.append((blk_name, blk_id, out_name, label))

        ins = []
        for input_name in self._inputs:
            if not q or q in input_name.lower():
                ins.append(input_name)

        # compute vertical centering inside panels
        def centered_start(count):
            if count <= 0: return top_y + 48  # fallback
            total = count * dy
            free  = col_h - total
            offset = max(36, free/2)  # keep some top padding even when many rows
            return top_y + offset

        y_out = centered_start(len(ups))
        y_in  = centered_start(len(ins))

        # headers positioned just above the first row, centered horizontally
        left_center  = margin + col_w/2
        right_center = margin + col_w + gap_x + col_w/2
        add_centered_header("Outputs", left_center,  y_out - header_gap_down)
        add_centered_header("Inputs",  right_center, y_in  - header_gap_down)

        # helper: label with a small bg so wires never strike through
        def add_label_with_bg(text, x, y, align="left"):
            t = sc.addSimpleText(text)
            t.setBrush(QColor("#333"))
            br = t.boundingRect()
            pad = 3
            bg = sc.addRect(0, 0, br.width() + pad*2, br.height() + pad*2,
                            QPen(Qt.PenStyle.NoPen), QColor("#FAFAFA"))
            bg.setZValue(2.5)
            t.setZValue(3.0)
            y_text = y - lift
            if align == "left":
                bg.setPos(x - br.width() - pad, y_text - pad)
                t.setPos(x - br.width(), y_text)
            else:
                bg.setPos(x - pad, y_text - pad)
                t.setPos(x, y_text)
            return t, bg

        # --- place outputs (left), labels to the LEFT of dot ---
        for (blk_name, blk_id, out_name, label) in ups:
            port = IOMapperDialog._PortCircle(left_x, y_out, dot_r, label, "out", (blk_id, out_name))
            sc.addItem(port); port.setZValue(3)
            add_label_with_bg(label, left_x - label_gap, y_out, align="left")
            self._port_items_out.append(port)
            y_out += dy

        # --- place inputs (right), labels to the RIGHT of dot ---
        for input_name in ins:
            port = IOMapperDialog._PortCircle(right_x, y_in, dot_r, input_name, "in", input_name)
            sc.addItem(port); port.setZValue(3)
            add_label_with_bg(input_name, right_x + label_gap, y_in, align="right")
            self._port_items_in.append(port)
            y_in += dy

        # restore saved wires
        saved = getattr(self.block, "input_mappings", {}) or {}
        for input_name, mapping in saved.items():
            blk_id = mapping.get("block_id")
            out_name = mapping.get("output_name") or mapping.get("output")
            src = self._find_out_port(blk_id, out_name)
            dst = self._find_in_port(input_name)
            if src and dst:
                self._add_wire(src, dst)


    def _find_out_port(self, blk_id, out_name):
        for p in self._port_items_out:
            bid, oname = p.payload
            if bid == blk_id and oname == out_name:
                return p
        return None

    def _find_in_port(self, input_name):
        for p in self._port_items_in:
            if p.payload == input_name:
                return p
        return None

    def _add_wire(self, src_port, dst_port):
        # remove existing wire for that input (1:1 mapping assumed)
        self._remove_wire_for_input(dst_port.payload)
        wire = IOMapperDialog._Wire(src_port, dst_port)
        self._wire_scene.addItem(wire)
        self._wires.append(wire)

    def _add_wire_by_ids(self, input_name, blk_id, out_name):
        src = self._find_out_port(blk_id, out_name)
        dst = self._find_in_port(input_name)
        if src and dst:
            self._add_wire(src, dst)

    def _remove_wire_for_input(self, input_name):
        for w in list(self._wires):
            if w.dst_port.payload == input_name:
                self._wire_scene.removeItem(w)
                self._wires.remove(w)

    def _delete_all_wires(self):
        for w in list(self._wires):
            self._wire_scene.removeItem(w)
        self._wires.clear()

    # Event filter for wire interactions
    def eventFilter(self, obj, event):
        if obj is self._wire_view.viewport():
            et = event.type()
            if et == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                pos = self._wire_view.mapToScene(event.pos())
                item = self._wire_scene.itemAt(pos, self._wire_view.transform())
                if isinstance(item, IOMapperDialog._PortCircle) and item.role == "out":
                    self._dragging_from = item
                    self._start_temp_path(item, pos)
                    return True
            elif et == event.Type.MouseMove and self._dragging_from:
                pos = self._wire_view.mapToScene(event.pos())
                self._update_temp_path(self._dragging_from, pos)
                return True
            elif et == event.Type.MouseButtonRelease and self._dragging_from:
                pos = self._wire_view.mapToScene(event.pos())
                item = self._wire_scene.itemAt(pos, self._wire_view.transform())
                if isinstance(item, IOMapperDialog._PortCircle) and item.role == "in":
                    self._add_wire(self._dragging_from, item)
                self._end_temp_path()
                self._dragging_from = None
                return True
        return super().eventFilter(obj, event)

    def _start_temp_path(self, src_port, pos):
        self._temp_path = QGraphicsPathItem()
        pen = QPen(QColor("#8A8A8A"), 2, Qt.PenStyle.DashLine)
        pen.setDashPattern([6, 4])
        self._temp_path.setPen(pen)
        self._wire_scene.addItem(self._temp_path)
        self._update_temp_path(src_port, pos)


    def _update_temp_path(self, src_port, pos):
        s = self._center(src_port)
        d = pos
        mid_x = (s.x() + d.x()) / 2.0
        path = QPainterPath(s)
        path.cubicTo(QPointF(mid_x, s.y()), QPointF(mid_x, d.y()), d)
        self._temp_path.setPath(path)

    def _end_temp_path(self):
        if self._temp_path:
            self._wire_scene.removeItem(self._temp_path)
            self._temp_path = None

    def _center(self, item):
        rect = item.rect(); return item.mapToScene(rect.center())

    # ======================
    # Mode + synchronization
    # ======================

    def _on_mode_change(self, val):
        # Before switching, sync from current view -> block.input_mappings (in-memory)
        if self.stack.currentIndex() == self.MODE_MENU:
            self._menu_to_mapping()
        else:
            self._wires_to_mapping()

        # Then apply that mapping into the other view
        self.stack.setCurrentIndex(val)
        if val == self.MODE_MENU:
            self._mapping_to_menu()
        else:
            self._mapping_to_wires()

    def _menu_to_mapping(self):
        m = {}
        for input_name, (_, combo) in self._rows.items():
            idx = combo.currentIndex()
            if idx <= 0:  # Not Connected
                continue
            data = combo.itemData(idx)
            if isinstance(data, tuple) and len(data) == 2:
                blk_id, out_name = data
                m[input_name] = {"block_id": blk_id, "output_name": out_name}
        self.block.input_mappings = m

    def _mapping_to_menu(self):
        saved = getattr(self.block, "input_mappings", {}) or {}
        for input_name, (_, combo) in self._rows.items():
            combo.setCurrentIndex(0)
            mapping = saved.get(input_name)
            if not mapping: 
                continue
            tgt_id = mapping.get("block_id")
            tgt_out = mapping.get("output_name") or mapping.get("output")
            for i in range(1, combo.count()):
                data = combo.itemData(i)
                if data and data == (tgt_id, tgt_out):
                    combo.setCurrentIndex(i); break

    def _wires_to_mapping(self):
        m = {}
        for w in self._wires:
            blk_id, out_name = w.src_port.payload
            input_name = w.dst_port.payload
            m[input_name] = {"block_id": blk_id, "output_name": out_name}
        self.block.input_mappings = m

    def _mapping_to_wires(self):
        self._delete_all_wires()
        saved = getattr(self.block, "input_mappings", {}) or {}
        for input_name, mapping in saved.items():
            blk_id = mapping.get("block_id"); out_name = mapping.get("output_name") or mapping.get("output")
            self._add_wire_by_ids(input_name, blk_id, out_name)

    def _load_saved_into_views(self):
        # MENU
        self._mapping_to_menu()
        # WIRE
        self._mapping_to_wires()

    # ======================
    # Save/close
    # ======================

    def _save_and_close(self):
        # Pull from current view into block.input_mappings
        if self.stack.currentIndex() == self.MODE_MENU:
            self._menu_to_mapping()
        else:
            self._wires_to_mapping()
        print("🔗 Saved input mappings:", getattr(self.block, "input_mappings", {}))
        self._toast("✅ Input mappings saved.")
        self.accept()

    def _toast(self, text: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("Saved")
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
 

