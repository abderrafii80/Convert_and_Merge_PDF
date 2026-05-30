import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QListWidget,
    QListWidgetItem, QListView, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QStyle
)

from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter, QPen, QBrush, QIcon
from PyQt6.QtCore import Qt, QSize


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)
from PyPDF2 import PdfReader
import fitz
import hashlib
import json
from datetime import datetime

from core.merger import merge_files
from core.utils import get_file_size_mb


def get_pdf_page_count(pdf_path):
    """Retourne le nombre de pages d'un PDF, ou None si erreur"""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except:
        return None


class FileCard(QFrame):
    def __init__(self, file_path, remove_callback):
        super().__init__()

        self.file_path = file_path
        self.remove_callback = remove_callback
        
        self.setObjectName("file_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAutoFillBackground(True)
        self.setFixedSize(190, 250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ================= PREVIEW =================
        preview = QLabel()
        preview.setFixedSize(170, 120)
        preview.setStyleSheet("""
            border-radius: 12px;
            background-color: #f7f7f7;
        """)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            if file_path.lower().endswith(".pdf"):
                page_count = get_pdf_page_count(file_path)
                pixmap = self.create_pdf_preview(page_count, file_path)
            else:
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    pixmap = self.create_image_placeholder()
        except:
            pixmap = self.create_image_placeholder()

        pixmap = pixmap.scaled(160, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        preview.setPixmap(pixmap)

        # ================= INFO =================
        info = QVBoxLayout()
        info.setSpacing(4)

        name = QLabel(os.path.basename(file_path))
        name_font = QFont()
        name_font.setPointSize(9)
        name_font.setBold(True)
        name.setFont(name_font)
        name.setStyleSheet("color: #333333;")
        name.setWordWrap(True)
        name.setFixedHeight(36)

        size_kb = os.path.getsize(file_path) / 1024
        if size_kb > 1024:
            size_text = f"{size_kb/1024:.2f} MB"
        else:
            size_text = f"{size_kb:.1f} KB"

        if file_path.lower().endswith(".pdf"):
            page_count = get_pdf_page_count(file_path)
            if page_count is not None:
                size_text = f"{size_text} - {page_count} page{'s' if page_count > 1 else ''}"

        size = QLabel(size_text)
        size_font = QFont()
        size_font.setPointSize(9)
        size.setFont(size_font)
        size.setStyleSheet("color: #666666;")

        ext = os.path.splitext(file_path)[1].upper().lstrip('.')
        ext_label = QLabel(ext)
        ext_font = QFont()
        ext_font.setPointSize(8)
        ext_label.setFont(ext_font)
        ext_label.setStyleSheet("color: #1e90ff; font-weight: bold;")

        info.addWidget(name)
        info.addWidget(size)
        info.addWidget(ext_label)
        info.addStretch()

        # ================= DELETE BUTTON =================
        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #ff3838;
            }
        """)
        btn_delete.clicked.connect(lambda: self.remove_callback(self))

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(btn_delete)

        layout.addLayout(top_bar)
        layout.addWidget(preview)
        layout.addLayout(info)

        self.setStyleSheet("""
            QFrame#file_card {
                background-color: white;
                border: 1px solid #1e90ff;
                border-radius: 14px;
            }
        """)
        self.setLayout(layout)

    def create_pdf_preview(self, page_count=None, pdf_path=None):
        """Génère une miniature de la première page d'un PDF sans écrire de cache."""
        try:
            # render with PyMuPDF
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            zoom = 150 / 72  # target ~150 DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes(output="png")
            qpix = QPixmap()
            qpix.loadFromData(img_bytes)

            # overlay page count
            if page_count is not None and not qpix.isNull():
                overlay = QPixmap(qpix)
                painter = QPainter(overlay)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                rect = overlay.rect()
                painter.fillRect(0, rect.height() - 24, rect.width(), 24, QColor(0, 0, 0, 140))
                font = QFont()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(QPen(QColor(255, 255, 255)))
                text = f"{page_count} page{'s' if page_count > 1 else ''}"
                painter.drawText(rect.adjusted(6, 0, -6, -4), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, text)
                painter.end()
                return overlay

            return qpix
        except Exception:
            # fallback simple drawn preview
            pixmap = QPixmap(180, 180)
            pixmap.fill(QColor(255, 255, 255))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            brush = QBrush(QColor(245, 245, 245))
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(10, 10, 160, 160, 12, 12)
            painter.setBrush(QBrush(QColor(220, 53, 69)))
            painter.drawRoundedRect(10, 10, 160, 36, 12, 12)
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont()
            font.setPointSize(18)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(20, 14, 140, 36, Qt.AlignmentFlag.AlignCenter, "PDF")
            if page_count is not None:
                painter.setPen(QPen(QColor(40, 40, 40)))
                count_font = QFont()
                count_font.setPointSize(9)
                count_font.setBold(True)
                painter.setFont(count_font)
                page_text = f"{page_count} page{'s' if page_count > 1 else ''}"
                painter.drawText(10, 130, 160, 20, Qt.AlignmentFlag.AlignCenter, page_text)
            painter.end()
            return pixmap

    def create_image_placeholder(self):
        """Crée un placeholder pour les images"""
        pixmap = QPixmap(180, 180)
        pixmap.fill(QColor(240, 240, 240))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRoundedRect(10, 10, 160, 160, 12, 12)
        painter.drawLine(20, 140, 60, 80)
        painter.drawLine(60, 80, 100, 120)
        painter.drawLine(100, 120, 140, 60)
        painter.end()
        return pixmap


class HistoryDialog(QDialog):
    """Fenêtre d'historique professionnelle — table avec export, clear, et ouverture de dossier."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des opérations")
        self.setMinimumSize(820, 520)

        # Cohérence visuelle avec la fenêtre principale
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QTableWidget { background-color: #fafafa; border: 1px solid #e8eef6; border-radius: 8px; }
            QHeaderView::section { background-color: #f0f8ff; padding: 6px; border: none; font-weight: bold; }
            QPushButton { background-color: transparent; color: #1e90ff; border: 1px solid #1e90ff; border-radius: 6px; padding: 6px 10px; }
            QPushButton:hover { background-color: #f0f8ff; }
        """)

        main = QVBoxLayout(self)

        # Header with search
        header_h = QHBoxLayout()
        title = QLabel("Historique")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_h.addWidget(title)

        header_h.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self.filter_history)
        header_h.addWidget(self.search)

        self.btn_export = QPushButton("Exporter JSON")
        self.btn_export.setToolTip("Exporter l'historique vers un fichier JSON")
        self.btn_export.clicked.connect(self.export_history)
        self.btn_export.setFixedHeight(34)
        self.btn_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        header_h.addWidget(self.btn_export)

        self.btn_clear = QPushButton("Effacer")
        self.btn_clear.setToolTip("Effacer tout l'historique (irréversible)")
        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_clear.setFixedHeight(34)
        # Use trash icon if available
        try:
            self.btn_clear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        except Exception:
            pass
        header_h.addWidget(self.btn_clear)

        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setFixedHeight(34)
        self.btn_close.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        header_h.addWidget(self.btn_close)

        main.addLayout(header_h)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Horodatage", "Opération", "Fichier(s)", "Nb", "Origine (MB)", "Final (MB)", "Sauvegardé"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._cell_double_clicked)
        self.table.setShowGrid(False)

        main.addWidget(self.table)

        # Footer with stats on the left and hint on the right
        footer_h = QHBoxLayout()
        self.stats_label = QLabel("")
        stats_font = QFont()
        stats_font.setPointSize(10)
        self.stats_label.setFont(stats_font)
        self.stats_label.setStyleSheet("color: #1e90ff; padding-left: 6px;")
        footer_h.addWidget(self.stats_label)

        footer_h.addStretch()
        hint = QLabel("Double-cliquez sur une ligne pour ouvrir le dossier du fichier sauvegardé.")
        hint.setStyleSheet("color: #666666; font-size: 11px; padding-top: 6px;")
        footer_h.addWidget(hint)
        main.addLayout(footer_h)

        self.load_history()

    def load_history(self):
        self.table.setRowCount(0)
        path = os.path.join("backup", "backup.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return

        # Fill table in reverse chronological order
        rows = list(reversed(data))
        self.table.setRowCount(len(rows))
        for r, entry in enumerate(rows):
            ts = entry.get('timestamp', '')
            op = entry.get('operation', '')
            fn = entry.get('filename', '')
            fc = str(entry.get('file_count', 0))
            orig = str(entry.get('original_size_mb', 0))
            fin = str(entry.get('final_size_mb', 0))
            saved = entry.get('saved_to', '')

            items = [ts, op, fn, fc, orig, fin, saved]
            for c, val in enumerate(items):
                it = QTableWidgetItem(val)
                if c in (4, 5):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                # Add a small folder icon to the saved path column
                if c == 6 and val:
                    try:
                        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
                        it.setIcon(icon)
                    except Exception:
                        pass
                self.table.setItem(r, c, it)

        # Adjust column widths for nicer layout
        self.table.resizeColumnsToContents()
        if self.table.columnCount() >= 3:
            self.table.setColumnWidth(2, max(300, self.table.columnWidth(2)))

        # Compute and display stats
        try:
            conversions = sum(1 for e in data if 'conversion' in e.get('operation', '').lower())
            merges = sum(1 for e in data if 'fusion' in e.get('operation', '').lower())
            total = len(data)
            self.stats_label.setText(f"Convertis: {conversions}   •   Fusionnés: {merges}   •   Total: {total}")
        except Exception:
            self.stats_label.setText("")

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter l'historique", os.path.join("backup", "backup_export.json"), "JSON Files (*.json)")
        if not path:
            return
        try:
            src = os.path.join("backup", "backup.json")
            if not os.path.exists(src):
                QMessageBox.information(self, "Aucun historique", "Aucun fichier d'historique trouvé.")
                return
            with open(src, 'r', encoding='utf-8') as f_in, open(path, 'w', encoding='utf-8') as f_out:
                data = json.load(f_in)
                json.dump(data, f_out, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Export réussi", f"Historique exporté vers:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur export", str(e))

    def clear_history(self):
        resp = QMessageBox.question(self, "Effacer l'historique", "Supprimer tout l'historique ? Cette action est irréversible.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            src = os.path.join("backup", "backup.json")
            if os.path.exists(src):
                os.remove(src)
            self.load_history()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def _cell_double_clicked(self, row, column):
        # Try to open the folder containing the 'saved_to' path for this row
        try:
            item = self.table.item(row, 6)
            if not item:
                return
            saved = item.text()
            if not saved:
                return
            # If it's a file path, open its folder; if it's not a path, ignore
            if os.path.exists(saved):
                folder = saved if os.path.isdir(saved) else os.path.dirname(saved)
                if folder and os.path.exists(folder):
                    try:
                        os.startfile(folder)
                    except Exception:
                        QMessageBox.information(self, "Ouvrir dossier", f"Chemin:\n{folder}")
            else:
                QMessageBox.information(self, "Chemin introuvable", f"Chemin enregistré:\n{saved}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def filter_history(self, text: str):
        """Simple row filter: hide rows that don't contain the search text in any cell."""
        text = text.lower().strip()
        for r in range(self.table.rowCount()):
            row_visible = False
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                if it and text in it.text().lower():
                    row_visible = True
                    break
            self.table.setRowHidden(r, not row_visible)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart PDF Fusion Pro")
        self.setGeometry(230, 100, 1100, 700)
        self.setMinimumSize(800, 600)

        self.files = []
        self.cleanup_temp_folder()

        # Set window icon from assets
        icon_path = resource_path(os.path.join('assets', 'ginger_96794.ico'))
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)

        # ================= MAIN LAYOUT =================
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ================= TITLE + HISTORY BUTTON =================
        top_h = QHBoxLayout()

        v_title = QVBoxLayout()
        title = QLabel("📄 Smart PDF Fusion Pro")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1e1e1e;")

        subtitle = QLabel("Fusionnez facilement vos PDF et images")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #666666; margin-bottom: 10px;")

        v_title.addWidget(title)
        v_title.addWidget(subtitle)

        top_h.addLayout(v_title)
        top_h.addStretch()

        right_buttons = QVBoxLayout()
        right_buttons.setSpacing(8)
        right_buttons.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_btn = QPushButton("Historique")
        self.history_btn.setFixedHeight(34)
        self.history_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #1e90ff; border: 1px solid #1e90ff; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background-color: #f0f8ff; }
        """)
        self.history_btn.clicked.connect(self.show_history)
        right_buttons.addWidget(self.history_btn)

        self.btn_clear_all = QPushButton("Effacer tout")
        self.btn_clear_all.setFixedHeight(34)
        self.btn_clear_all.setStyleSheet("""
            QPushButton { background-color: #f0f8ff; color: #1e90ff; border: 1px solid #1e90ff; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background-color: #e0f2ff; }
        """)
        self.btn_clear_all.clicked.connect(self.clear_selection)
        right_buttons.addWidget(self.btn_clear_all)

        top_h.addLayout(right_buttons)

        main_layout.addLayout(top_h)

        # ================= LIST =================
        list_label = QLabel("Fichiers à fusionner :")
        list_label_font = QFont()
        list_label_font.setPointSize(11)
        list_label_font.setBold(True)
        list_label.setFont(list_label_font)
        list_label.setStyleSheet("color: #333333;")
        main_layout.addWidget(list_label)

        # ================= ORDER DISPLAY =================
        self.order_label = QLabel("Aucun fichier sélectionné")
        order_font = QFont()
        order_font.setPointSize(10)
        self.order_label.setFont(order_font)
        self.order_label.setStyleSheet("color: #1e90ff; font-weight: bold; padding: 8px; background-color: #f0f8ff; border-radius: 6px; border-left: 4px solid #1e90ff;")
        self.order_label.setWordWrap(True)
        main_layout.addWidget(self.order_label)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setFlow(QListView.Flow.LeftToRight)
        self.list_widget.setMovement(QListView.Movement.Snap)
        self.list_widget.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_widget.setWrapping(True)
        self.list_widget.setGridSize(QSize(205, 285))
        self.list_widget.setSpacing(24)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.update_order_display)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #fafafa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 14px;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                margin: 6px;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QListView::item {
                background: transparent;
            }
        """)
        main_layout.addWidget(self.list_widget)

        # ================= BUTTONS =================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_add = QPushButton("➕ Select files")
        self.btn_add.setMinimumHeight(45)
        self.btn_add.setFont(self._button_font())
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1978d9;
            }
            QPushButton:pressed {
                background-color: #1860bb;
            }
        """)
        self.btn_add.clicked.connect(self.add_files)

        self.btn_merge = QPushButton(" Merge PDF")
        self.btn_merge.setMinimumHeight(45)
        self.btn_merge.setFont(self._button_font())
        self.btn_merge.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:pressed:enabled {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)
        self.btn_merge.clicked.connect(self.handle_action)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_merge)

        main_layout.addLayout(btn_layout)

        # ================= STATUS =================
        self.label = QLabel("")
        label_font = QFont()
        label_font.setPointSize(11)
        self.label.setFont(label_font)
        self.label.setStyleSheet("""
            color: #28a745;
            font-weight: bold;
            padding: 10px;
            background-color: #f0f9f5;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        """)
        self.label.setVisible(False)
        main_layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(main_layout)
        container.setStyleSheet("background-color: #ffffff;")
        self.setCentralWidget(container)

        # ================= MAIN WINDOW STYLE =================
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
        """)

        self.update_button_state()

    def _button_font(self):
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font

    # ================= TEMP CLEANUP =================
    def cleanup_temp_folder(self):
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            return
        for entry in os.listdir(temp_dir):
            path = os.path.join(temp_dir, entry)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
            except Exception:
                pass

    # ================= UPDATE =================
    def update_button_state(self):
        file_count = len(self.files)
        
        if file_count == 0:
            self.btn_merge.setText("Merge PDF")
            self.btn_merge.setEnabled(False)
        elif file_count == 1:
            file_path = self.files[0]
            if file_path.lower().endswith(".pdf"):
                self.btn_merge.setText("✓ Fichier converti PDF")
                self.btn_merge.setEnabled(False)
            else:
                self.btn_merge.setText("📄 Convertir à PDF")
                self.btn_merge.setEnabled(True)
        else:
            self.btn_merge.setText("🚀 Fusionner")
            self.btn_merge.setEnabled(True)
        
        self.update_order_display()

    def update_order_display(self):
        """Met à jour l'affichage de l'ordre des fichiers"""
        if self.list_widget.count() == 0:
            self.order_label.setText("Aucun fichier sélectionné")
            return

        order_list = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                filename = os.path.basename(widget.file_path)
                order_list.append(f"{i + 1}. {filename}")

        if order_list:
            self.order_label.setText(" → ".join(order_list))
        else:
            self.order_label.setText("Aucun fichier sélectionné")

    def show_history(self):
        dlg = HistoryDialog(self)
        dlg.exec()

    # ================= ADD FILES =================
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Ajouter fichiers",
            "",
            "PDF & Images (*.png *.jpg *.jpeg *.pdf)"
        )

        for f in files:
            self.files.append(f)

            item = QListWidgetItem()
            card = FileCard(f, self.remove_card)

            item.setSizeHint(QSize(190, 250))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, card)

        self.update_button_state()
        self.update_order_display()

    # ================= REMOVE FILE =================
    def remove_card(self, card_widget):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)

            if widget == card_widget:
                self.list_widget.takeItem(i)
                self.files.pop(i)
                break

        self.update_button_state()
        self.update_order_display()
        self.label.setVisible(False)

    def clear_selection(self):
        if self.list_widget.count() == 0:
            return
        self.list_widget.clear()
        self.files = []
        self.update_button_state()
        self.update_order_display()
        self.label.setVisible(False)

    # ================= HANDLE ACTION =================
    def handle_action(self):
        """Décide entre conversion d'image ou fusion de PDF"""
        if len(self.files) == 1:
            file_path = self.files[0]
            if not file_path.lower().endswith(".pdf"):
                self.convert_to_pdf(file_path)
        else:
            self.merge()
    
    # ================= CONVERT TO PDF =================
    def convert_to_pdf(self, image_path):
        """Convertit une image en PDF et demande où sauvegarder"""
        try:
            from PIL import Image

            # Ouverture de l'image
            img = Image.open(image_path)

            # Conversion en RGB si nécessaire (pour PNG avec alpha, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Default filename
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            default_path = os.path.join("output", f"{name_without_ext}.pdf")

            # Ask user where to save
            save_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le PDF", default_path, "PDF Files (*.pdf)")
            if not save_path:
                return

            os.makedirs(os.path.dirname(save_path) or "output", exist_ok=True)
            img.save(save_path, 'PDF')

            size = get_file_size_mb(save_path)

            # Sauvegarde du backup
            original_size = os.path.getsize(image_path) / (1024 * 1024)
            file_ext = os.path.splitext(image_path)[1].upper().lstrip('.')
            self.save_backup(
                filename=filename,
                original_size=original_size,
                file_type=file_ext,
                final_size=size,
                file_count=1,
                operation="Conversion à PDF",
                saved_to=save_path
            )

            self.label.setText(
                f"✔ Conversion réussie ! {filename} → {size:.2f} MB"
            )
            self.label.setVisible(True)
        except Exception as e:
            self.label.setText(f"✗ Erreur : {str(e)}")
            self.label.setVisible(True)

    # ================= SAVE BACKUP =================
    def save_backup(self, filename, original_size, file_type, final_size, file_count, operation, saved_to=None):
        """Sauvegarde les métadonnées dans un fichier JSON
        saved_to: chemin final du fichier résultant (optionnel)
        """
        os.makedirs("backup", exist_ok=True)
        backup_file = "backup/backup.json"
        
        # Charger les données existantes ou créer une nouvelle liste
        backup_data = []
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            except:
                backup_data = []
        
        # Créer l'entrée
        computed_saved = None
        if saved_to:
            computed_saved = saved_to
        else:
            computed_saved = "output/" + os.path.splitext(filename)[0] + (".pdf" if operation == "Conversion à PDF" else "final.pdf")

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "filename": filename,
            "file_type": file_type,
            "original_size_mb": round(original_size, 2),
            "final_size_mb": round(final_size, 2),
            "file_count": file_count,
            "saved_to": computed_saved
        }
        
        # Ajouter à la liste
        backup_data.append(entry)
        
        # Sauvegarder dans JSON
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde backup: {e}")

    # ================= MERGE =================
    def merge(self):
        # ordre UI → ordre files
        ordered_files = []

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            ordered_files.append(widget.file_path)

        # Demander où sauvegarder le PDF fusionné
        default_path = os.path.join("output", "final.pdf")
        save_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le PDF fusionné", default_path, "PDF Files (*.pdf)")
        if not save_path:
            return

        os.makedirs(os.path.dirname(save_path) or "output", exist_ok=True)
        merge_files(ordered_files, save_path)

        size = get_file_size_mb(save_path)

        # Calculer la taille totale originale
        total_original_size = sum(os.path.getsize(f) / (1024 * 1024) for f in ordered_files)

        # Creer le nom des fichiers pour le backup
        file_names = " + ".join([os.path.basename(f) for f in ordered_files])

        # Sauvegarde du backup
        self.save_backup(
            filename=file_names,
            original_size=total_original_size,
            file_type="MERGED",
            final_size=size,
            file_count=len(ordered_files),
            operation="Fusion de PDF",
            saved_to=save_path
        )

        self.label.setText(
            f"✔ Fusion réussie ! {len(ordered_files)} fichiers → {size:.2f} MB"
        )
        self.label.setVisible(True)