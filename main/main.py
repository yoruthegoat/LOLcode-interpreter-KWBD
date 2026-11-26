import grammar_func, syntax_func, semantic_func


class TerminalOutput:
    # passed to the semantic analyzer as its output, prints VISIBLE right away
    def append(self, text):
        print(text, end="", flush=True)


def askInput(name):
    # GIMMEH reads one line from the terminal
    try:
        return input()
    except EOFError:
        return ""


def main():
    fileName = input("Enter the .lol file path: ").strip()
    try:
        with open(fileName, "r", encoding="utf-8-sig") as fp:
            source = fp.read()
    except (OSError, UnicodeError) as error:
        print("Cannot read file:", error)
        return

    # milestone 1 lexical analyzer
    scannedTokens, errors = grammar_func.scan(source)
    if len(errors) > 0:
        for line, message in errors:
            print("Error on line", str(line) + ":", message)
        return

    # milestone 2 syntax analyzer
    lines, error = syntax_func.parse(scannedTokens)
    print(syntax_func.printTree(lines))
    if error is not None:
        print("\n" + str(error))
        return
    print("\nNo syntax errors.\n")

    # milestone 3 semantic analyzer (runs the program)
    variables = {"IT": None}
    try:
        error = semantic_func.run(scannedTokens, variables, TerminalOutput(), askInput)
    except RecursionError:
        error = "Semantic error - Maximum recursion depth exceeded"
    if error is not None:
        print("\n" + str(error))

    print("\nSymbol table:")
    for name, value in variables.items():
        print(" ", name, "=", semantic_func.formatValue(value), "(" + semantic_func.getType(value) + ")")


if __name__ == "__main__":
    main()
