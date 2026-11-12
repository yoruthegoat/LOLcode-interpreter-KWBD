# CMSC 124 milestone 3 (semantic analyzer)

import math as mathLib
import grammar_func as grammar
import syntax_func as syntax


def semanticError(tokens, pos, message):
    # report the line where the semantic check failed
    if pos < len(tokens):
        message = "Semantic error on line " + str(tokens[pos][2]) + " - " + message
    else:
        message = "Semantic error - " + message
    return message


def getType(value):
    # check bool first because python also treats it as an integer
    if value is None:
        return "NOOB"
    if type(value) is bool:
        return "TROOF"
    if type(value) is int:
        return "NUMBR"
    if type(value) is float:
        return "NUMBAR"
    return "YARN"


def getValue(tokens, pos, variables):
    # read a literal or the current value of a variable
    if pos >= len(tokens):
        return None, pos, semanticError(tokens, pos, "Expected a value")
    text, tokenType, line = tokens[pos]

    if tokenType == "String Delimiter":
        return tokens[pos + 1][0], pos + 3, None

    if tokenType == "Variable Identifier":
        if text not in variables:
            return None, pos, semanticError(tokens, pos, "Undeclared variable: " + text)
        return variables[text], pos + 1, None

    if tokenType == "Literal":
        if text == "WIN":
            return True, pos + 1, None
        if text == "FAIL":
            return False, pos + 1, None

        # check the numeric text before converting it
        if grammar.classify(text) != "Literal":
            return None, pos, semanticError(tokens, pos, "Cannot read numeric literal: " + text)
        if "." in text:
            value = float(text)
        else:
            # build the integer one digit at a time
            value = 0
            for digit in text.lstrip("-"):
                value = value * 10 + int(digit)
            if text.startswith("-"):
                value = -value
        if type(value) is float and not mathLib.isfinite(value):
            return None, pos, semanticError(tokens, pos, "NUMBAR literal is too large")
        return value, pos + 1, None

    return None, pos, semanticError(tokens, pos, "Expression is not supported yet: " + text)


def toYarn(value, tokens, pos):
    # convert a value for visible
    valueType = getType(value)
    if valueType == "NOOB":
        return "", semanticError(tokens, pos, "Cannot implicitly cast NOOB to YARN")
    if valueType == "TROOF":
        return ("WIN" if value else "FAIL"), None
    if valueType == "NUMBR":
        # convert each digit without a size limit
        if value == 0:
            return "0", None
        number = abs(value)
        digits = []
        while number > 0:
            digits.append(str(number % 10))
            number //= 10
        digits.reverse()
        text = "".join(digits)
        if value < 0:
            text = "-" + text
        return text, None
    if valueType == "NUMBAR":
        # keep up to two decimal places without rounding
        text = str(value)
        if "e" in text.lower():
            text = format(value, "f")
        point = text.find(".")
        return text[:point + 3], None
    return str(value), None


def declaration(tokens, pos, variables):
    # add a variable after checking its name and initial value
    name = tokens[pos + 1][0]
    if name in variables:
        return pos, semanticError(tokens, pos + 1, "Variable already declared: " + name)
    pos += 2
    value = None
    if syntax.word(tokens, pos) == "ITZ":
        value, pos, error = getValue(tokens, pos + 1, variables)
        if error:
            return pos, error
    variables[name] = value
    return pos, None


def statement(tokens, pos, variables, outputLines):
    # handle basic output, assignment, and expression statements
    text = syntax.word(tokens, pos)
    tokenType = syntax.getTokenType(tokens, pos)

    if text == "VISIBLE":
        pos += 1
        valuePos = pos
        value, pos, error = getValue(tokens, pos, variables)
        if error:
            return pos, error
        text, error = toYarn(value, tokens, valuePos)
        if error:
            return pos, error
        parts = [text]
        while syntax.getTokenType(tokens, pos) == "Output Separator":
            pos += 1
            valuePos = pos
            value, pos, error = getValue(tokens, pos, variables)
            if error:
                return pos, error
            text, error = toYarn(value, tokens, valuePos)
            if error:
                return pos, error
            parts.append(text)
        outputLines.append("".join(parts))

    elif tokenType == "Variable Identifier" and syntax.word(tokens, pos + 1) == "R":
        # assignment may change the variable's type
        name = tokens[pos][0]
        if name not in variables:
            return pos, semanticError(tokens, pos, "Undeclared variable: " + name)
        value, pos, error = getValue(tokens, pos + 2, variables)
        if error:
            return pos, error
        variables[name] = value

    elif tokenType == "Variable Identifier" and syntax.word(tokens, pos + 1) == "IS NOW A":
        return pos, semanticError(tokens, pos, "Typecasting is not supported yet")

    elif tokenType in ["Literal", "String Delimiter", "Variable Identifier"]:
        # store a standalone value in the implicit variable
        value, pos, error = getValue(tokens, pos, variables)
        if error:
            return pos, error
        variables["IT"] = value

    else:
        return pos, semanticError(tokens, pos, "Statement is not supported yet: " + text)

    return pos, None


def analyze(tokens):
    # start each run with a fresh symbol table
    variables = {"IT": None}
    outputLines = []

    # finish syntax checks before changing any values
    lines, error = syntax.parse(tokens)
    if error:
        return variables, outputLines, error
    tokens = [token for token in tokens if token[1] != "Comment Delimiter"]

    # functions outside the program belong to a later step
    if syntax.word(tokens, 0) != "HAI":
        error = semanticError(tokens, 0, "Function definitions are not supported yet")
        return variables, outputLines, error
    pos = 1

    if syntax.word(tokens, pos) == "WAZZUP":
        pos += 1
        while syntax.word(tokens, pos) == "I HAS A":
            pos, error = declaration(tokens, pos, variables)
            if error:
                return variables, outputLines, error
        pos += 1  # buhbye

    while syntax.word(tokens, pos) != "KTHXBYE":
        pos, error = statement(tokens, pos, variables, outputLines)
        if error:
            return variables, outputLines, error
    pos += 1
    if pos < len(tokens):
        error = semanticError(tokens, pos, "Function definitions are not supported yet")
        return variables, outputLines, error

    return variables, outputLines, None


# todo
# - arithmetic operations
# - boolean operations
# - comparison operations
# - string concatenation
# - implicit and explicit typecasting
# - user input
# - if-else statements
# - switch-case statements
# - loops and break statements
# - functions, local scope, and return values
