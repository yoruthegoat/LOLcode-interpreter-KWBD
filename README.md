# CMSC 124 - LOLCODE INTERPRETER

Kids with Big Dreams | S2L

Contributors: see [contributors.txt](contributors.txt).

Runs LOLCODE programs with lexical, syntax, and semantic analysis. Displays tokens, a syntax tree, program output, and a symbol table.

Requires Python 3. The GUI also needs PySide6. Checked locally with Python 3.13.13 and PySide6 6.12.0.

Run from the project folder containing `main`.

On Linux/macOS, set up PySide6 once:

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

On Windows, set up and launch the GUI:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install PySide6
.\.venv\Scripts\python.exe main\gui.py
```

After the first Windows setup, repeat only the last command to launch.

Click **Select .lol file**, choose a file from `testcases_fixed`, then click **Run**. You can edit the code before running. Enter requested input in the dialog, and use **Stop** to end a running program.

Testcase folders:

- `testcases`: original supplied examples.
- `testcases_fixed`: corrected examples for normal runs.
- `testcases_bonus`: five simple bonus examples, with expected output in comments.

For terminal execution (no extra packages needed), run `python3 main/main.py` on Linux/macOS or `py main/main.py` on Windows.

When asked for a file path, enter `testcases_fixed/01_variables.lol`. The terminal displays the syntax tree, program output, and final symbol table. Enter any requested input directly in the terminal.
