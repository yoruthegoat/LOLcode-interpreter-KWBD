import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QFileDialog, QInputDialog, QHeaderView, QTreeWidget, QTreeWidgetItem, QTabWidget
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt
import grammar_func, syntax_func, semantic_func

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
QPushButton:disabled {
    background-color: #3c3c3c;
    color: #888888;
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

class ConsoleOutput:
    # passed to the semantic analyzer as its output, so VISIBLE shows up right away
    def __init__(self, console):
        self.console = console

    def append(self, text):
        self.console.moveCursor(QTextCursor.End)
        self.console.insertPlainText(text)
        self.console.moveCursor(QTextCursor.End)
        QApplication.processEvents()


class LiveVariables(dict):
    # the symbol table used during a run, it reports every new or changed value to the window
    def __init__(self, onChange):
        super().__init__()
        self.onChange = onChange
        self["IT"] = None

    def __setitem__(self, name, value):
        super().__setitem__(name, value)
        self.onChange(name, value)


class StopRun(Exception):
    # raised inside a run when the Stop button was pressed
    pass


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

        # Stop Button (only enabled while a program runs)
        self.stopButton = QPushButton("Stop")
        self.stopButton.setEnabled(False)
        self.stopRequested = False
        self.steps = 0
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
        self.symbolTable = QTableWidget(0, 3)
        self.symbolTable.setHorizontalHeaderLabels(["Identifier", "Value", "Type"])
        self.symbolRows = {}    # variable name -> its row in the symbol table

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
        topRow.addWidget(self.stopButton)

        # Right Column (tokens and symbol table side by side, parse tree below)
        tableSplit = QSplitter(Qt.Horizontal)
        tableSplit.addWidget(self.tokenTable)
        tableSplit.addWidget(self.symbolTable)

        rightSplit = QSplitter(Qt.Vertical)
        rightSplit.addWidget(tableSplit)
        rightSplit.addWidget(self.treeWidget)
        rightSplit.setSizes([400, 200])

        # Horizontal Splitter (Source editor: left , Inspection panels: right)
        middleSplit = QSplitter(Qt.Horizontal)
        middleSplit.addWidget(self.codeEdit)
        middleSplit.addWidget(rightSplit)

        # Vertical Splitter (Code/Panels: top , Console output: bottom)
        mainSplit = QSplitter(Qt.Vertical)
        mainSplit.addWidget(middleSplit)
        mainSplit.addWidget(self.console)
        mainSplit.setSizes([450, 250])

        layout = QVBoxLayout()
        layout.addLayout(topRow)
        layout.addWidget(mainSplit)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        # -----------------------------------------------------------------------------

        self.openButton.clicked.connect(self.onOpen)
        self.runButton.clicked.connect(self.onRun)
        self.stopButton.clicked.connect(self.onStop)

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
        self.symbolRows = {}
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
        lines, error = syntax_func.parse(scanned)
        self.fillTree(lines)
        if error:
            self.console.appendPlainText(str(error))
            return

        # Semantic analysis (runs the program)
        # the symbol table fills itself as values change (see LiveVariables)
        variables = LiveVariables(self.updateSymbol)
        self.stopRequested = False
        self.steps = 0
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        try:
            error = semantic_func.run(scanned, variables, ConsoleOutput(self.console),
                                      self.askInput, self.onStep)
        except RecursionError:
            error = "Semantic error - Maximum recursion depth exceeded"
        except StopRun:
            error = "Program stopped by the user"
        finally:
            self.runButton.setEnabled(True)
            self.stopButton.setEnabled(False)
        if error:
            self.printLine(str(error))

    def onStep(self):
        # called before every statement, lets the window redraw and the Stop button work
        self.steps += 1
        if self.steps % 200 == 0:
            QApplication.processEvents()
        if self.stopRequested:
            raise StopRun()

    def onStop(self):
        self.stopRequested = True

    def closeEvent(self, event):
        # closing the window also ends a running program
        self.stopRequested = True
        event.accept()

    def askInput(self, name):
        # GIMMEH: ask for the input in a dialog
        text, ok = QInputDialog.getText(self, "GIMMEH", "Enter a value for " + name + ":")
        if not ok:
            text = ""
        # echo the input so the console reads like a terminal
        ConsoleOutput(self.console).append(text + "\n")
        return text

    def printLine(self, text):
        # start on a new line if the last VISIBLE ended with !
        current = self.console.toPlainText()
        if current and not current.endswith("\n"):
            text = "\n" + text
        ConsoleOutput(self.console).append(text + "\n")

    def fillTokens(self, tokens):
        # Populate the lexical token table widget
        self.tokenTable.setRowCount(len(tokens))
        for row, token in enumerate(tokens):
            self.tokenTable.setItem(row, 0, QTableWidgetItem(str(token[0])))
            self.tokenTable.setItem(row, 1, QTableWidgetItem(str(token[1])))

    def updateSymbol(self, name, value):
        # add a new variable as a row, or update the row of an existing one
        row = self.symbolRows.get(name)
        if row is None:
            row = self.symbolTable.rowCount()
            self.symbolTable.insertRow(row)
            self.symbolRows[name] = row
            self.symbolTable.setItem(row, 0, QTableWidgetItem(name))
            self.symbolTable.setItem(row, 1, QTableWidgetItem())
            self.symbolTable.setItem(row, 2, QTableWidgetItem())
        self.symbolTable.item(row, 1).setText(semantic_func.formatValue(value))
        self.symbolTable.item(row, 2).setText(semantic_func.getType(value))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())