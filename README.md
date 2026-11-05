# CMSC 124 - LOLCODE INTERPRETER

Kids with Big Dreams | S2L

Reads a LOLCODE file, identifies tokens, and displays its syntax tree.

MILESTONE 2

Run from the project folder. For the GUI, set up PySide6 once:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PySide6
```

Launch the GUI:

```bash
source .venv/bin/activate
python main/gui.py
```

Click **Select .lol file**, choose a file from `testcases`, then click **Run**.

For terminal-only analysis (no extra packages needed):

```bash
python3 main/main.py
```

When asked for a file path, enter `testcases/01_variables.lol`.
