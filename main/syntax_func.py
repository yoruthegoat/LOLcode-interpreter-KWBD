# CMSC 124 milestone 2 (syntax analyzer)

from grammar_func import scan

# All operations except SMOOSH, ALL OF, ANY OF, and NOT are binary
BINARY = ["SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF", "BIGGR OF",
          "SMALLR OF", "BOTH OF", "EITHER OF", "WON OF", "BOTH SAEM", "DIFFRINT"]

def saveLine(lines, depth, text):
    lines.append([depth, text])

def word(tokens, pos):
    # text of the current token (empty if it is a literal value like 12 or "hi")
    if pos < len(tokens) and tokens[pos][1] != "Literal":
        return tokens[pos][0]
    return ""

def getTokenType(tokens, pos):
    # classification of the current token
    if pos < len(tokens):
        return tokens[pos][1]
    return ""

def syntaxError(tokens, pos, lines, message):
    # stop parsing and pass the message to the gui or terminal
    if pos < len(tokens):
        errorMessage = ("Syntax error on line " + str(tokens[pos][2]) + " - " + message
                        + " (found '" + tokens[pos][0] + "')")
    else:
        errorMessage = "Syntax error - " + message + " (the file ended too early)"
    raise SystemExit(errorMessage)


def hasMoreSiblings(lines, i, d):
    # checks if theres another sibling before going back up
    for j in range(i + 1, len(lines)):
        if lines[j][0] < d:
            return False
        if lines[j][0] == d:
            return True
    return False

def printTree(lines):
    out = []
    for i in range(len(lines)):
        depth = lines[i][0]
        prefix = ""
        # vertical bars of the parent levels
        for j in range(1, depth):
            prefix += "│   " if hasMoreSiblings(lines, i, j) else "    "
        prefix += "├── " if hasMoreSiblings(lines, i, depth) else "└── "
        out.append(prefix + lines[i][1])
    return "\n".join(out)

def nextToken(tokens, pos, lines, depth):
    # add the current token to the tree and return the position of the next token
    if pos >= len(tokens):
        syntaxError(tokens, pos, lines, "Expected more code")   
    saveLine(lines, depth, tokens[pos][1] + ": " + tokens[pos][0])
    return pos + 1

def expectToken(tokens, pos, lines, depth, expected):
    # checks if the current token is the required token follow up from the previous token
    if word(tokens, pos) != expected:
        syntaxError(tokens, pos, lines, "Expected " + expected)
    return nextToken(tokens, pos, lines, depth)

def expectType(tokens, pos, lines, depth):
    # checks if the classification of the current token is a type literal
    if getTokenType(tokens, pos) != "Type Literal":
        syntaxError(tokens, pos, lines, "Expected a type like NUMBR or YARN")
    return nextToken(tokens, pos, lines, depth)

def checkEndOfLine(tokens, pos, lines):
    # makes sure nothing else comes after a statement
    if pos < len(tokens) and tokens[pos][2] == tokens[pos - 1][2]:
        syntaxError(tokens, pos, lines, "Expected end of line")

def checkSameLine(tokens, start, pos, lines):
    # keep the whole statement on one line
    if tokens[pos - 1][2] != tokens[start][2]:
        syntaxError(tokens, start, lines, "A statement or expression must stay on one line")

def expression(tokens, pos, lines, depth, allowVariadic=True):
    # read the expression then check its line
    start = pos
    pos = expressionValue(tokens, pos, lines, depth, allowVariadic)
    checkSameLine(tokens, start, pos, lines)
    return pos

def expressionValue(tokens, pos, lines, depth, allowVariadic):
    # check what kind of expression follows
    text = word(tokens, pos)
    tokenType = getTokenType(tokens, pos)

    if tokenType == "String Delimiter":
        # check the text and closing quote
        saveLine(lines, depth, "<String>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "Literal":
            syntaxError(tokens, pos, lines, "Expected string contents")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "String Delimiter":
            syntaxError(tokens, pos, lines, "Expected a closing quote")
        pos = nextToken(tokens, pos, lines, depth + 1)

    elif tokenType == "Literal" or tokenType == "Variable Identifier":
        pos = nextToken(tokens, pos, lines, depth)

    elif text in BINARY:
        # false prevents infinite arity operations inside operands
        saveLine(lines, depth, "<" + text + ">")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1, False)
        pos = expectToken(tokens, pos, lines, depth + 1, "AN")
        pos = expression(tokens, pos, lines, depth + 1, False)

    elif text == "NOT":
        saveLine(lines, depth, "<NOT>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1, False)

    elif text == "ALL OF" or text == "ANY OF":
        # do not allow these inside another operand
        if not allowVariadic:
            syntaxError(tokens, pos, lines, "ALL OF and ANY OF cannot be nested in an operand")
        saveLine(lines, depth, "<" + text + ">")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1, False)
        while word(tokens, pos) == "AN":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1, False)
        pos = expectToken(tokens, pos, lines, depth + 1, "MKAY")

    elif text == "SMOOSH":
        # do not allow concatenation inside another operand
        if not allowVariadic:
            syntaxError(tokens, pos, lines, "SMOOSH cannot be nested in an operand")
        saveLine(lines, depth, "<SMOOSH>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1, False)
        while word(tokens, pos) == "AN":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1, False)
        # mkay is optional for smoosh
        if word(tokens, pos) == "MKAY":
            pos = nextToken(tokens, pos, lines, depth + 1)

    elif text == "MAEK":
        saveLine(lines, depth, "<MAEK>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1, False)
        # a is optional between the value and type
        if word(tokens, pos) == "A":
            pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expectType(tokens, pos, lines, depth + 1)

    elif text == "I IZ":
        saveLine(lines, depth, "<Function Call>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "Function Identifier":
            syntaxError(tokens, pos, lines, "Expected a function name")
        pos = nextToken(tokens, pos, lines, depth + 1)   #function name
        # read arguments after yr
        if word(tokens, pos) == "YR":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1, False)
            while word(tokens, pos) == "AN":
                pos = nextToken(tokens, pos, lines, depth + 1)
                pos = expectToken(tokens, pos, lines, depth + 1, "YR")
                pos = expression(tokens, pos, lines, depth + 1, False)
        # every function call must end with mkay
        pos = expectToken(tokens, pos, lines, depth + 1, "MKAY")

    else:
        syntaxError(tokens, pos, lines, "Expected an expression")

    return pos

def codeBlock(tokens, pos, lines, depth, stopWords, inFunction=False,
              canBreak=False, allowFunctions=False):
    # read till stop word is found
    # pass the same function and break rules to each statement
    saveLine(lines, depth, "<Code Block>")
    while pos < len(tokens) and word(tokens, pos) not in stopWords and word(tokens, pos) != "KTHXBYE":
        pos = statement(tokens, pos, lines, depth + 1, inFunction, canBreak, allowFunctions)
    return pos

def declaration(tokens, pos, lines, depth):
    # read the variable name and optional initial value
    start = pos
    saveLine(lines, depth, "<Variable Declaration>")
    pos = nextToken(tokens, pos, lines, depth + 1)
    if getTokenType(tokens, pos) != "Variable Identifier":
        syntaxError(tokens, pos, lines, "Expected a variable name")
    pos = nextToken(tokens, pos, lines, depth + 1)
    if word(tokens, pos) == "ITZ":
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
    checkSameLine(tokens, start, pos, lines)
    checkEndOfLine(tokens, pos, lines)
    return pos

def variableSection(tokens, pos, lines, depth):
    # read declarations between wazzup and buhbye
    saveLine(lines, depth, "<Variable Section>")
    pos = expectToken(tokens, pos, lines, depth + 1, "WAZZUP")
    checkEndOfLine(tokens, pos, lines)
    while word(tokens, pos) == "I HAS A":
        pos = declaration(tokens, pos, lines, depth + 1)
    pos = expectToken(tokens, pos, lines, depth + 1, "BUHBYE")
    checkEndOfLine(tokens, pos, lines)
    return pos

def statement(tokens, pos, lines, depth, inFunction=False, canBreak=False,
              allowFunctions=True):
    # remember where the statement starts
    start = pos
    text = word(tokens, pos)
    tokenType = getTokenType(tokens, pos)

    after = ""
    if pos + 1 < len(tokens):
        after = tokens[pos + 1][0]

    if text == "VISIBLE":
        saveLine(lines, depth, "<Print Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        # output values are separated by plus signs
        while getTokenType(tokens, pos) == "Output Separator":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif text == "GIMMEH":
        saveLine(lines, depth, "<Input Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "Variable Identifier":
            syntaxError(tokens, pos, lines, "Expected a variable")
        pos = nextToken(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif tokenType == "Variable Identifier" and after == "R":
        saveLine(lines, depth, "<Assignment Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif tokenType == "Variable Identifier" and after == "IS NOW A":
        saveLine(lines, depth, "<Typecast Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expectType(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif text == "O RLY?":
        saveLine(lines, depth, "<If-Then Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)
        pos = expectToken(tokens, pos, lines, depth + 1, "YA RLY")
        checkEndOfLine(tokens, pos, lines)
        pos = codeBlock(tokens, pos, lines, depth + 1, ["NO WAI", "OIC"], inFunction, canBreak)
        if word(tokens, pos) == "NO WAI":
            pos = nextToken(tokens, pos, lines, depth + 1)
            checkEndOfLine(tokens, pos, lines)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OIC"], inFunction, canBreak)
        pos = expectToken(tokens, pos, lines, depth + 1, "OIC")
        checkEndOfLine(tokens, pos, lines)

    elif text == "WTF?":
        saveLine(lines, depth, "<Switch-Case Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)
        if word(tokens, pos) != "OMG":
            syntaxError(tokens, pos, lines, "Expected OMG")
        while word(tokens, pos) == "OMG":
            # keep each case value on the same line as omg
            caseStart = pos
            pos = nextToken(tokens, pos, lines, depth + 1)
            if getTokenType(tokens, pos) != "Literal" and getTokenType(tokens, pos) != "String Delimiter":
                syntaxError(tokens, pos, lines, "Expected a literal after OMG")
            pos = expression(tokens, pos, lines, depth + 1)
            checkSameLine(tokens, caseStart, pos, lines)
            checkEndOfLine(tokens, pos, lines)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OMG", "OMGWTF", "OIC"], inFunction, True)
        if word(tokens, pos) == "OMGWTF":
            pos = nextToken(tokens, pos, lines, depth + 1)
            checkEndOfLine(tokens, pos, lines)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OIC"], inFunction, True)
        pos = expectToken(tokens, pos, lines, depth + 1, "OIC")
        checkEndOfLine(tokens, pos, lines)

    elif text == "IM IN YR":
        saveLine(lines, depth, "<Loop Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "Loop Identifier":
            syntaxError(tokens, pos, lines, "Expected a loop label")
        # save the opening label for comparison later
        label = word(tokens, pos)
        pos = nextToken(tokens, pos, lines, depth + 1)  # loop label
        if word(tokens, pos) != "UPPIN" and word(tokens, pos) != "NERFIN":
            syntaxError(tokens, pos, lines, "Expected UPPIN or NERFIN")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expectToken(tokens, pos, lines, depth + 1, "YR")
        if getTokenType(tokens, pos) != "Variable Identifier":
            syntaxError(tokens, pos, lines, "Expected a loop variable")
        pos = nextToken(tokens, pos, lines, depth + 1)  # variable
        if word(tokens, pos) == "TIL" or word(tokens, pos) == "WILE":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)
        checkSameLine(tokens, start, pos, lines)
        checkEndOfLine(tokens, pos, lines)
        pos = codeBlock(tokens, pos, lines, depth + 1, ["IM OUTTA YR"], inFunction, True)
        endStart = pos
        pos = expectToken(tokens, pos, lines, depth + 1, "IM OUTTA YR")
        # the closing label must match the opening label
        if getTokenType(tokens, pos) != "Loop Identifier" or word(tokens, pos) != label:
            syntaxError(tokens, pos, lines, "Expected matching loop label " + label)
        pos = nextToken(tokens, pos, lines, depth + 1)  # loop label
        checkSameLine(tokens, endStart, pos, lines)
        checkEndOfLine(tokens, pos, lines)

    elif text == "HOW IZ I":
        # functions cannot be defined inside other blocks
        if not allowFunctions or inFunction:
            syntaxError(tokens, pos, lines, "Functions must be defined at program level")
        saveLine(lines, depth, "<Function Definition>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if getTokenType(tokens, pos) != "Function Identifier":
            syntaxError(tokens, pos, lines, "Expected a function name")
        pos = nextToken(tokens, pos, lines, depth + 1)  # function name
        # read parameter names after yr
        if word(tokens, pos) == "YR":
            pos = nextToken(tokens, pos, lines, depth + 1)
            if getTokenType(tokens, pos) != "Variable Identifier":
                syntaxError(tokens, pos, lines, "Expected a parameter name")
            pos = nextToken(tokens, pos, lines, depth + 1)  # first parameter
            while word(tokens, pos) == "AN":
                pos = nextToken(tokens, pos, lines, depth + 1)
                pos = expectToken(tokens, pos, lines, depth + 1, "YR")
                if getTokenType(tokens, pos) != "Variable Identifier":
                    syntaxError(tokens, pos, lines, "Expected a parameter name")
                pos = nextToken(tokens, pos, lines, depth + 1)  # next parameter
        checkSameLine(tokens, start, pos, lines)
        checkEndOfLine(tokens, pos, lines)
        pos = codeBlock(tokens, pos, lines, depth + 1, ["IF U SAY SO"], True)
        pos = expectToken(tokens, pos, lines, depth + 1, "IF U SAY SO")
        checkEndOfLine(tokens, pos, lines)

    elif text == "GTFO":
        # check if there is a block to exit
        if not canBreak and not inFunction:
            syntaxError(tokens, pos, lines, "GTFO needs a loop, switch, or function")
        saveLine(lines, depth, "<Break Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif text == "FOUND YR":
        # return is only allowed inside a function
        if not inFunction:
            syntaxError(tokens, pos, lines, "FOUND YR needs a function")
        saveLine(lines, depth, "<Return Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    else:
        # reaching here means it has to be an expression
        saveLine(lines, depth, "<Expression Statement>")
        pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    # simple statements must finish on their starting line
    if text not in ["O RLY?", "WTF?", "IM IN YR", "HOW IZ I"]:
        checkSameLine(tokens, start, pos, lines)
    return pos


def program(tokens, lines):
    pos = 0
    saveLine(lines, 1, "<Program>")
    # functions may appear before hai
    while word(tokens, pos) == "HOW IZ I":
        pos = statement(tokens, pos, lines, 2)
    pos = expectToken(tokens, pos, lines, 2, "HAI")
    checkEndOfLine(tokens, pos, lines)

    if word(tokens, pos) == "WAZZUP":
        # read the optional variable section
        pos = variableSection(tokens, pos, lines, 2)

    pos = codeBlock(tokens, pos, lines, 2, [], allowFunctions=True)
    pos = expectToken(tokens, pos, lines, 2, "KTHXBYE")
    checkEndOfLine(tokens, pos, lines)
    # functions may also appear after kthxbye
    while word(tokens, pos) == "HOW IZ I":
        pos = statement(tokens, pos, lines, 2)
    # reject any other code after the program ends
    if pos < len(tokens):
        syntaxError(tokens, pos, lines, "Unexpected code after KTHXBYE")

def parse(tokens):
    lines = []
    try:
        # check comment lines before removing the comment tokens
        codeTokens = []
        for pos, token in enumerate(tokens):
            if token[1] == "Comment Delimiter":
                if token[0] == "OBTW" or token[0] == "TLDR":
                    if pos > 0 and tokens[pos - 1][2] == token[2]:
                        syntaxError(tokens, pos, lines, "Block comment delimiters need their own line")
                    if pos + 1 < len(tokens) and tokens[pos + 1][2] == token[2]:
                        # only a btw comment can follow the delimiter
                        if tokens[pos + 1][0] != "BTW" or tokens[pos + 1][1] != "Comment Delimiter":
                            syntaxError(tokens, pos + 1, lines, "Block comment delimiters need their own line")
            else:
                codeTokens.append(token)
        tokens = codeTokens
        program(tokens, lines)
        return lines, None
    except SystemExit as error:
        return lines, str(error)
    except RecursionError:
        return lines, "Syntax error - Maximum recursion depth exceeded"
