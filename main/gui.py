import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QFileDialog, QInputDialog, QHeaderView, QTreeWidget, QTreeWidgetItem, QTabWidget
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import grammar_func, syntax_func, interpreter_func

THEME = """
QMainWindow {
    background-color: #1e1e1e;
}

/* General Text Color */
QWidget {
    color: #cccccc;
    font-family: "Montserrat", sans-serif;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background-color: #2A835F;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #12544F;
}
QPushButton:pressed {
    background-color: #094771;
}

/* Text Editors & Console */
QPlainTextEdit {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}

/* Tables */
QTableWidget {
    background-color: #252526;
    gridline-color: #333333;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #12544F;
    color: #ffffff;
    padding: 4px;
    border: none;
    font-weight: bold;
}

/* Tree Widget */
QTreeWidget {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QTreeWidget::item:selected {
    background-color: #094771;
}

/* Splitter Handles */
QSplitter::handle {
    background-color: #333333;
    margin: 2px;
}
QSplitter::handle:hover {
    background-color: #0e639c;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #12544F;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
}

"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOLcode Interpreter by KWBD")
        self.resize(1200, 750)
        self.setStyleSheet(THEME)


        # -----------------------------------------------------------------------------
        # Top Control Bar Widgets
        # -----------------------------------------------------------------------------
        # Select file button
        self.openButton = QPushButton("Select .lol file")
        self.pathLabel = QLabel("No file selected")
        
        # Run Button
        self.runButton = QPushButton("Run")
        # -----------------------------------------------------------------------------



        # -----------------------------------------------------------------------------
        # Code Editor & Inspection Panels
        # -----------------------------------------------------------------------------
        # Editor for LOLcode source code
        self.codeEdit = QPlainTextEdit()
        self.codeEdit.setFont(QFont("Consolas", 12))

        # Token table
        self.tokenTable = QTableWidget(0, 2)
        self.tokenTable.setHorizontalHeaderLabels(["Lexeme", "Classification"])

        # Symbols table
        self.symbolTable = QTableWidget(0, 2)
        self.symbolTable.setHorizontalHeaderLabels(["Symbol", "Value"])

        # Tree view for parse tree
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(["Parse Tree"])

        for table in (self.tokenTable, self.symbolTable):
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
        # -----------------------------------------------------------------------------



        # -----------------------------------------------------------------------------
        # Console Output Panel
        # -----------------------------------------------------------------------------
        # Console table
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 11))
        # -----------------------------------------------------------------------------



        # -----------------------------------------------------------------------------
        # Layout Panels
        # -----------------------------------------------------------------------------

        # Top Row Header Bar
        topRow = QHBoxLayout()
        topRow.setSpacing(10)
        topRow.addWidget(self.openButton)
        topRow.addWidget(self.pathLabel, 1)
        topRow.addWidget(self.runButton)

        # Right Column
        rightSplit = QSplitter(Qt.Vertical)
        rightSplit.addWidget(self.tokenTable)
        # Hide the symbol table for now
        # rightSplit.addWidget(self.symbolTable)
        rightSplit.addWidget(self.treeWidget)

        # Horizontal Splitter (Source editor: left , Inspection panels: right)
        middleSplit = QSplitter(Qt.Horizontal)
        middleSplit.addWidget(self.codeEdit)
        middleSplit.addWidget(rightSplit)

        # Vertical Splitter (Code/Panels: top , Console output: bottom)
        mainSplit = QSplitter(Qt.Vertical)
        mainSplit.addWidget(middleSplit)
        mainSplit.addWidget(self.console)
        mainSplit.setSizes([500, 100])

        layout = QVBoxLayout()
        layout.addLayout(topRow)
        layout.addWidget(mainSplit)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        # -----------------------------------------------------------------------------

        self.openButton.clicked.connect(self.onOpen)
        self.runButton.clicked.connect(self.onRun)

    def fillTree(self, lines):
        # Populates the parse tree widget with hierarchal depth nodes
        self.treeWidget.clear()
        lastAtDepth = {}
        for depth, text in lines:
            parent = lastAtDepth.get(depth - 1, self.treeWidget.invisibleRootItem())
            lastAtDepth[depth] = QTreeWidgetItem(parent, [text])
        self.treeWidget.expandAll()

    def onOpen(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open LOLCODE file", "", "LOLCODE (*.lol);;All files (*)")
        if path:
            with open(path, "r", encoding="utf-8-sig") as fp:
                self.codeEdit.setPlainText(fp.read())
            self.pathLabel.setText(path)
    
    def onRun(self):
        self.console.clear()    # Reset output views for every run
        self.tokenTable.setRowCount(0)
        self.symbolTable.setRowCount(0)
        self.treeWidget.clear()

        # Fetch source code from editor
        source = self.codeEdit.toPlainText()          

        # Lexical analysis
        scanned, errors = grammar_func.scan(source)
        self.fillTokens(scanned)        
              
        if errors:
            for line, message in errors:
                self.console.appendPlainText(f"Error on line {line}: {message}")
            return

        # Syntax Analysis
        tokens = [t for t in scanned if t[1] != "Comment Delimiter"]
        lines, error = syntax_func.parse(tokens)
        self.fillTree(lines)
        if error:
            self.console.appendPlainText(str(error))
            return

    def fillTokens(self, tokens):
        # Populate the lexical token table widget
        self.tokenTable.setRowCount(len(tokens))
        for row, token in enumerate(tokens):
            self.tokenTable.setItem(row, 0, QTableWidgetItem(str(token[0])))
            self.tokenTable.setItem(row, 1, QTableWidgetItem(str(token[1])))

    # Not implemented yet
    """def fillSymbols(self, variables):             
        self.symbolTable.setRowCount(len(variables))
        for row, (name, value) in enumerate(variables.items()):
            self.symbolTable.setItem(row, 0, QTableWidgetItem(name))
            self.symbolTable.setItem(row, 1, QTableWidgetItem(str(value)))"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())