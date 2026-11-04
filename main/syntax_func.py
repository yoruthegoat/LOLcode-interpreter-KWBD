#CMSC 124 milestone 2 (syntax analyzer)

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
    # prints the parse tree obtained so far
    printTree(lines)
    if pos < len(tokens): # prints the error then exits
        print("\nSyntax error on line", tokens[pos][2], "-", message, "(found '" + tokens[pos][0] + "')")
    else:
        print("\nSyntax error -", message, "(the file ended too early)")
    exit()


def hasMoreSiblings(lines, i, d):
    # checks if theres another sibling before going back up
    for j in range(i + 1, len(lines)):
        if lines[j][0] < d:
            return False
        if lines[j][0] == d:
            return True
    return False

def printTree(lines):
    for i in range(len(lines)):
        depth = lines[i][0]
        prefix = ""
        # vertical bars of the parent levels
        for j in range(1, depth):
            if hasMoreSiblings(lines, i, j):
                prefix += "│   "
            else:
                prefix += "    "
        # the branch of this line
        if hasMoreSiblings(lines, i, depth):
            prefix += "├── "
        else:
            prefix += "└── "
        print(prefix + lines[i][1])

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


def expression(tokens, pos, lines, depth):
    text = word(tokens, pos)
    tokenType = getTokenType(tokens, pos)

    if tokenType == "String Delimiter":
        saveLine(lines, depth, "<String>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)

    elif tokenType == "Literal" or tokenType == "Variable Identifier":
        pos = nextToken(tokens, pos, lines, depth)

    elif text in BINARY:
        saveLine(lines, depth, "<" + text + ">")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        pos = expectToken(tokens, pos, lines, depth + 1, "AN")
        pos = expression(tokens, pos, lines, depth + 1)

    elif text == "NOT":
        saveLine(lines, depth, "<NOT>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)

    elif text == "ALL OF" or text == "ANY OF":
        saveLine(lines, depth, "<" + text + ">")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        while word(tokens, pos) == "AN":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)
        pos = expectToken(tokens, pos, lines, depth + 1, "MKAY")

    elif text == "SMOOSH":
        saveLine(lines, depth, "<SMOOSH>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        pos = expectToken(tokens, pos, lines, depth + 1, "AN")
        pos = expression(tokens, pos, lines, depth + 1)
        while word(tokens, pos) == "AN":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)

    elif text == "MAEK":
        saveLine(lines, depth, "<MAEK>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if word(tokens, pos) == "A":
            pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        if word(tokens, pos) == "A":
            pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expectType(tokens, pos, lines, depth + 1)

    elif text == "I IZ":
        saveLine(lines, depth, "<Function Call>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)   #function name
        if word(tokens, pos) == "YR":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)
            while word(tokens, pos) == "AN":
                pos = nextToken(tokens, pos, lines, depth + 1)
                pos = expectToken(tokens, pos, lines, depth + 1, "YR")
                pos = expression(tokens, pos, lines, depth + 1)
        if word(tokens, pos) == "MKAY":
            pos = nextToken(tokens, pos, lines, depth + 1)

    else:
        syntaxError(tokens, pos, lines, "Expected an expression")

    return pos

def codeBlock(tokens, pos, lines, depth, stopWords):
    # read till stop word is found
    saveLine(lines, depth, "<Code Block>")
    while pos < len(tokens) and word(tokens, pos) not in stopWords and word(tokens, pos) != "KTHXBYE":
        pos = statement(tokens, pos, lines, depth + 1)
    return pos

def statement(tokens, pos, lines, depth):
    text = word(tokens, pos)
    tokenType = getTokenType(tokens, pos)

    after = ""
    if pos + 1 < len(tokens):
        after = tokens[pos + 1][0]

    if text == "VISIBLE":
        saveLine(lines, depth, "<Print Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        while getTokenType(tokens, pos) == "Output Separator" or word(tokens, pos) == "AN":
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
        pos = expectToken(tokens, pos, lines, depth + 1, "YA RLY")
        pos = codeBlock(tokens, pos, lines, depth + 1, ["NO WAI", "OIC"])
        if word(tokens, pos) == "NO WAI":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OIC"])
        pos = expectToken(tokens, pos, lines, depth + 1, "OIC")

    elif text == "WTF?":
        saveLine(lines, depth, "<Switch-Case Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        if word(tokens, pos) != "OMG":
            syntaxError(tokens, pos, lines, "Expected OMG")
        while word(tokens, pos) == "OMG":
            pos = nextToken(tokens, pos, lines, depth + 1)
            if getTokenType(tokens, pos) != "Literal" and getTokenType(tokens, pos) != "String Delimiter":
                syntaxError(tokens, pos, lines, "Expected a literal after OMG")
            pos = expression(tokens, pos, lines, depth + 1)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OMG", "OMGWTF", "OIC"])
        if word(tokens, pos) == "OMGWTF":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = codeBlock(tokens, pos, lines, depth + 1, ["OIC"])
        pos = expectToken(tokens, pos, lines, depth + 1, "OIC")

    elif text == "IM IN YR":
        saveLine(lines, depth, "<Loop Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)  # loop label
        if word(tokens, pos) != "UPPIN" and word(tokens, pos) != "NERFIN":
            syntaxError(tokens, pos, lines, "Expected UPPIN or NERFIN")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expectToken(tokens, pos, lines, depth + 1, "YR")
        pos = nextToken(tokens, pos, lines, depth + 1)  # variable
        if word(tokens, pos) == "TIL" or word(tokens, pos) == "WILE":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = expression(tokens, pos, lines, depth + 1)
        pos = codeBlock(tokens, pos, lines, depth + 1, ["IM OUTTA YR"])
        pos = expectToken(tokens, pos, lines, depth + 1, "IM OUTTA YR")
        pos = nextToken(tokens, pos, lines, depth + 1)  # loop label

    elif text == "HOW IZ I":
        saveLine(lines, depth, "<Function Definition>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = nextToken(tokens, pos, lines, depth + 1)  # function name
        if word(tokens, pos) == "YR":
            pos = nextToken(tokens, pos, lines, depth + 1)
            pos = nextToken(tokens, pos, lines, depth + 1)  # first parameter
            while word(tokens, pos) == "AN":
                pos = nextToken(tokens, pos, lines, depth + 1)
                pos = expectToken(tokens, pos, lines, depth + 1, "YR")
                pos = nextToken(tokens, pos, lines, depth + 1)  # next parameter
        pos = codeBlock(tokens, pos, lines, depth + 1, ["IF U SAY SO"])
        pos = expectToken(tokens, pos, lines, depth + 1, "IF U SAY SO")

    elif text == "GTFO":
        saveLine(lines, depth, "<Break Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    elif text == "FOUND YR":
        saveLine(lines, depth, "<Return Statement>")
        pos = nextToken(tokens, pos, lines, depth + 1)
        pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    else:
        # reaching here means it has to be an expression
        saveLine(lines, depth, "<Expression Statement>")
        pos = expression(tokens, pos, lines, depth + 1)
        checkEndOfLine(tokens, pos, lines)

    return pos



def program(tokens, lines):
    pos = 0
    saveLine(lines, 1, "<Program>")
    pos = expectToken(tokens, pos, lines, 2, "HAI")

    if word(tokens, pos) == "WAZZUP":
        saveLine(lines, 2, "<Variable Section>")
        pos = nextToken(tokens, pos, lines, 3)
        while word(tokens, pos) == "I HAS A":
            saveLine(lines, 3, "<Variable Declaration>")
            pos = nextToken(tokens, pos, lines, 4)
            if getTokenType(tokens, pos) != "Variable Identifier":
                syntaxError(tokens, pos, lines, "Expected a variable name")
            pos = nextToken(tokens, pos, lines, 4)
            if word(tokens, pos) == "ITZ":
                pos = nextToken(tokens, pos, lines, 4)
                pos = expression(tokens, pos, lines, 4)
            checkEndOfLine(tokens, pos, lines)
        pos = expectToken(tokens, pos, lines, 3, "BUHBYE")

    pos = codeBlock(tokens, pos, lines, 2, [])
    pos = expectToken(tokens, pos, lines, 2, "KTHXBYE")