import grammar_func, syntax_func;

def main():
    fileName = input("Enter the .lol file path: ").strip()
    try:
        with open(fileName, "r", encoding="utf-8-sig") as fp:
            source = fp.read()
    except (OSError, UnicodeError) as error:
        print("Cannot read file:", error)
        return

    # milestone 1 lexical analyzer
    scannedTokens, errors = syntax_func.scan(source)
    if len(errors) > 0:
        for line, message in errors:
            print("Error on line", str(line) + ":", message)
        return

    # ignore comments
    tokens = []
    for token in scannedTokens:
        if token[1] != "Comment Delimiter":
            tokens.append(token)

    lines = []
    syntax_func.program(tokens, lines)
    syntax_func.printTree(lines)
    print("\nNo syntax errors.")


if __name__ == "__main__":
    main()