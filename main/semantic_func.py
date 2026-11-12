# CMSC 124 milestone 3 (semantic analyzer)

import math as mathLib
import grammar_func as grammar
import syntax_func as syntax

ARITHMETIC = ["SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF"]
BOOLEAN = ["BOTH OF", "EITHER OF", "WON OF"]
COMPARISON = ["BOTH SAEM", "DIFFRINT"]
BLOCK_ENDS = {"O RLY?": "OIC", "WTF?": "OIC", "IM IN YR": "IM OUTTA YR", "HOW IZ I": "IF U SAY SO"}

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


def getValue(tokens, pos, variables, outputLines, askInput, functions):
    # read a literal, a variable, or the result of an expression
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
        value, error = toNumber(text, tokens, pos)
        return value, pos + 1, error

    if text in ARITHMETIC or text in BOOLEAN or text in COMPARISON:
        # binary operations, the operands are read left to right
        operatorPos = pos
        left, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
        if error:
            return None, pos, error
        right, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)  # skips AN
        if error:
            return None, pos, error

        if text in ARITHMETIC:
            value, error = arithmetic(text, left, right, tokens, operatorPos)
            return value, pos, error
        if text in BOOLEAN:
            return boolean(text, left, right), pos, None
        if text == "BOTH SAEM":
            return isEqual(left, right), pos, None
        return not isEqual(left, right), pos, None

    if text == "NOT":
        value, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
        if error:
            return None, pos, error
        return not toTroof(value), pos, None

    if text == "ALL OF" or text == "ANY OF":
        # keep reading operands until there is no AN, then skip MKAY
        operator = text
        results = []
        pos += 1
        while True:
            value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
            if error:
                return None, pos, error
            results.append(toTroof(value))
            if syntax.word(tokens, pos) != "AN":
                break
            pos += 1
        pos += 1
        if operator == "ALL OF":
            return all(results), pos, None
        return any(results), pos, None

    if text == "SMOOSH":
        # every operand is cast to a YARN and joined
        parts = []
        pos += 1
        while True:
            valuePos = pos
            value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
            if error:
                return None, pos, error
            piece, error = toYarn(value, tokens, valuePos)
            if error:
                return None, pos, error
            parts.append(piece)
            if syntax.word(tokens, pos) != "AN":
                break
            pos += 1
        return "".join(parts), pos, None

    if text == "MAEK":
        # maek [a] value [a] type
        operatorPos = pos
        pos += 1
        if syntax.word(tokens, pos) == "A":
            pos += 1
        value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
        if error:
            return None, pos, error
        if syntax.word(tokens, pos) == "A":
            pos += 1
        value, error = castTo(value, tokens[pos][0], tokens, operatorPos)
        return value, pos + 1, error

    if text == "I IZ":
        return callFunction(tokens, pos, variables, outputLines, askInput, functions)

    return None, pos, semanticError(tokens, pos, "Cannot evaluate: " + text)


def callFunction(tokens, pos, variables, outputLines, askInput, functions):
    # run a function and give back its return value
    name = tokens[pos + 1][0]
    if name not in functions:
        return None, pos, semanticError(tokens, pos + 1, "Undefined function: " + name)
    callPos = pos
    pos += 2

    # the arguments are evaluated first, using the caller's variables
    arguments = []
    if syntax.word(tokens, pos) == "YR":
        value, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
        if error:
            return None, pos, error
        arguments.append(value)
        while syntax.word(tokens, pos) == "AN":
            value, pos, error = getValue(tokens, pos + 2, variables, outputLines, askInput, functions)  # skips AN YR
            if error:
                return None, pos, error
            arguments.append(value)
    if syntax.word(tokens, pos) == "MKAY":
        pos += 1

    parameters, bodyPos = functions[name]
    if len(arguments) != len(parameters):
        message = ("Function " + name + " needs " + str(len(parameters))
                   + " argument(s) but got " + str(len(arguments)))
        return None, pos, semanticError(tokens, callPos + 1, message)

    # the function can only see its own parameters
    localVariables = {"IT": None}
    for i in range(len(parameters)):
        localVariables[parameters[i]] = arguments[i]
    endPos, signal, error = codeBlock(tokens, bodyPos, localVariables, outputLines, askInput, functions, ["IF U SAY SO"])
    if error:
        return None, pos, error

    # no found yr or a gtfo gives back a noob, the result is also stored in IT
    result = None
    if signal == "RETURN":
        result = localVariables["IT"]
    variables["IT"] = result
    return result, pos, None


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


def toNumber(text, tokens, pos):
    # read numeric text as a NUMBR or NUMBAR
    if text in ["WIN", "FAIL"] or grammar.classify(text) != "Literal":
        return 0, semanticError(tokens, pos, "Cannot convert to a number: " + text)
    if "." in text:
        value = float(text)
        if not mathLib.isfinite(value):
            return 0, semanticError(tokens, pos, "NUMBAR literal is too large")
        return value, None
 
    # build the integer one digit at a time
    value = 0
    for digit in text.lstrip("-"):
        value = value * 10 + int(digit)
    if text.startswith("-"):
        value = -value
    return value, None


def toFloat(value, tokens, pos):
    # huge NUMBR wont fit in a NUMBAR
    try:
        return float(value), None
    except OverflowError:
        return 0.0, semanticError(tokens, pos, "NUMBR is too large to become a NUMBAR")
    

def toNumeric(value, tokens, pos):
    # implicit cast to a number for math operations
    valueType = getType(value)
    if valueType == "NOOB":
        return 0, semanticError(tokens, pos, "Cannot implicitly cast NOOB to a number")
    if valueType == "TROOF":
        return (1 if value else 0), None
    if valueType == "YARN":
        return toNumber(value, tokens, pos)
    return value, None


def toTroof(value):
    # never fails since every type can be cast to TROOF
    valueType = getType(value)
    if valueType == "NOOB":
        return False
    if valueType == "TROOF":
        return value
    if valueType == "YARN":
        return value != ""
    return value != 0


def castTo(value, typeName, tokens, pos):
    # explicit cast (only the returned value changes)
    valueType = getType(value)
    if typeName == "NOOB":
        return None, None
    if typeName == "TROOF":
        return toTroof(value), None
    if typeName == "YARN":
        # noob becomes an empty string when explicitly cast
        if valueType == "NOOB":
            return "", None
        return toYarn(value, tokens, pos)

    # noob becomes zero when explicitly cast
    number = 0
    if valueType != "NOOB":
        number, error = toNumeric(value, tokens, pos)
        if error:
            return None, error
    if typeName == "NUMBR":
        # cuts off the decimal part
        if type(number) is float:
            number = int(number)
        return number, None
    return toFloat(number, tokens, pos)


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


def codeBlock(tokens, pos, variables, outputLines, askInput, functions, stopWords):
    # run statements until a stop word, a gtfo or found yr ends the block early
    while pos < len(tokens) and syntax.word(tokens, pos) not in stopWords and syntax.word(tokens, pos) != "KTHXBYE":
        pos, signal, error = statement(tokens, pos, variables, outputLines, askInput, functions)
        if error:
            return pos, "", error
        if signal != "":
            return pos, signal, None
    return pos, "", None


def statement(tokens, pos, variables, outputLines, askInput, functions):
    # run one statement, signal is BREAK after gtfo and RETURN after found yr
    text = syntax.word(tokens, pos)
    tokenType = syntax.getTokenType(tokens, pos)
    signal = ""

    if text == "VISIBLE":
        pos += 1
        valuePos = pos
        value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
        if error:
            return pos, "", error
        text, error = toYarn(value, tokens, valuePos)
        if error:
            return pos, "", error
        parts = [text]
        while syntax.getTokenType(tokens, pos) == "Output Separator" or syntax.word(tokens, pos) == "AN":
            pos += 1
            valuePos = pos
            value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
            if error:
                return pos, "", error
            text, error = toYarn(value, tokens, valuePos)
            if error:
                return pos, "", error
            parts.append(text)
        outputLines.append("".join(parts))

    elif text == "GIMMEH":
        name = tokens[pos + 1][0]
        if name not in variables:
            return pos, "", semanticError(tokens, pos + 1, "Undeclared variable: " + name)
        # the input is always a yarn
        value = askInput()
        if value is None:
            value = ""
        variables[name] = value
        pos += 2

    elif tokenType == "Variable Identifier" and syntax.word(tokens, pos + 1) == "R":
        # assignment may change the variable's type
        name = tokens[pos][0]
        if name not in variables:
            return pos, "", semanticError(tokens, pos, "Undeclared variable: " + name)
        value, pos, error = getValue(tokens, pos + 2, variables, outputLines, askInput, functions)
        if error:
            return pos, "", error
        variables[name] = value

    elif tokenType == "Variable Identifier" and syntax.word(tokens, pos + 1) == "IS NOW A":
        # recast the variable itself
        name = tokens[pos][0]
        if name not in variables:
            return pos, "", semanticError(tokens, pos, "Undeclared variable: " + name)
        value, error = castTo(variables[name], tokens[pos + 2][0], tokens, pos)
        if error:
            return pos, "", error
        variables[name] = value
        pos += 3

    elif text == "O RLY?":
        # run the YA RLY part if IT is WIN, otherwise run the NO WAI part
        pos += 2
        if toTroof(variables["IT"]):
            pos, signal, error = codeBlock(tokens, pos, variables, outputLines, askInput, functions, ["NO WAI", "OIC"])
            if error:
                return pos, "", error
        else:
            pos = skipBlock(tokens, pos, ["NO WAI", "OIC"])
            if syntax.word(tokens, pos) == "NO WAI":
                pos, signal, error = codeBlock(tokens, pos + 1, variables, outputLines, askInput, functions, ["OIC"])
                if error:
                    return pos, "", error
        # skip the part that did not run and the OIC
        pos = skipBlock(tokens, pos, ["OIC"]) + 1

    elif text == "WTF?":
        # compare IT to each case, once one matches the cases below it run too until a GTFO
        pos += 1
        matched = False
        while syntax.word(tokens, pos) == "OMG":
            caseValue, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
            if error:
                return pos, "", error
            if isEqual(variables["IT"], caseValue):
                matched = True
            if matched and signal == "":
                pos, signal, error = codeBlock(tokens, pos, variables, outputLines, askInput, functions, ["OMG", "OMGWTF", "OIC"])
                if error:
                    return pos, "", error
            else:
                pos = skipBlock(tokens, pos, ["OMG", "OMGWTF", "OIC"])

        # the default case only runs if none of the cases matched
        if syntax.word(tokens, pos) == "OMGWTF" and not matched:
            pos, signal, error = codeBlock(tokens, pos + 1, variables, outputLines, askInput, functions, ["OIC"])
            if error:
                return pos, "", error
        pos = skipBlock(tokens, pos, ["OIC"]) + 1

        # gtfo only leaves the switch, found yr keeps going up
        if signal == "BREAK":
            signal = ""

    elif text == "IM IN YR":
        # im in yr label uppin yr variable [til|wile condition]
        headerPos = pos
        operation = syntax.word(tokens, pos + 2)
        name = tokens[pos + 4][0]
        if name not in variables:
            return pos, "", semanticError(tokens, pos + 4, "Undeclared variable: " + name)
        pos += 5
        conditionType = syntax.word(tokens, pos)
        if conditionType != "TIL" and conditionType != "WILE":
            conditionType = ""
        loopStart = pos
        bodyPos = pos

        while True:
            pos = loopStart
            # the condition is checked before every run of the body
            if conditionType != "":
                value, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
                if error:
                    return pos, "", error
                bodyPos = pos
                condition = toTroof(value)
                # til stops once the condition is true, wile stops once it is false
                if conditionType == "TIL" and condition:
                    break
                if conditionType == "WILE" and not condition:
                    break
            pos, signal, error = codeBlock(tokens, pos, variables, outputLines, askInput, functions, ["IM OUTTA YR"])
            if error:
                return pos, "", error
            if signal != "":
                break

            # uppin and nerfin work on the number value of the variable
            number, error = toNumeric(variables[name], tokens, headerPos)
            if error:
                return pos, "", error
            if operation == "UPPIN":
                variables[name] = number + 1
            else:
                variables[name] = number - 1

        # continue after im outta yr and its label
        pos = skipBlock(tokens, bodyPos, ["IM OUTTA YR"]) + 2
        if signal == "BREAK":
            signal = ""

    elif text == "HOW IZ I":
        # the function was already collected, skip over its body
        pos = skipBlock(tokens, pos + 1, ["IF U SAY SO"]) + 1

    elif text == "GTFO":
        pos += 1
        signal = "BREAK"

    elif text == "FOUND YR":
        # the return value is stored in IT of the function
        value, pos, error = getValue(tokens, pos + 1, variables, outputLines, askInput, functions)
        if error:
            return pos, "", error
        variables["IT"] = value
        signal = "RETURN"

    else:
        # anything else is an expression, its result goes to the implicit variable
        value, pos, error = getValue(tokens, pos, variables, outputLines, askInput, functions)
        if error:
            return pos, "", error
        variables["IT"] = value

    return pos, signal, None


def skipBlock(tokens, pos, stopWords):
    # skip to the next stop word, blocks inside the skipped code are passed over
    depth = 0
    while pos < len(tokens):
        text = syntax.word(tokens, pos)
        if depth == 0 and text in stopWords:
            return pos
        if text in BLOCK_ENDS:
            depth += 1
        elif text in BLOCK_ENDS.values() and depth > 0:
            depth -= 1
        pos += 1
    return pos


def findFunctions(tokens):
    # collect every function before running so a call can come before its definition
    functions = {}
    pos = 0
    while pos < len(tokens):
        if syntax.word(tokens, pos) == "HOW IZ I":
            name = tokens[pos + 1][0]
            if name in functions:
                return functions, semanticError(tokens, pos + 1, "Function already defined: " + name)
            pos += 2
            parameters = []
            if syntax.word(tokens, pos) == "YR":
                parameters.append(tokens[pos + 1][0])
                pos += 2
                while syntax.word(tokens, pos) == "AN":
                    parameters.append(tokens[pos + 2][0])
                    pos += 3
            functions[name] = (parameters, pos)
        else:
            pos += 1
    return functions, None


def run(tokens, variables, outputLines, askInput):
    # run the program after the syntax check, returns an error message or None
    functions, error = findFunctions(tokens)
    if error:
        return error
    pos = 1

    if syntax.word(tokens, pos) == "WAZZUP":
        pos += 1
        while syntax.word(tokens, pos) == "I HAS A":
            pos, error = declaration(tokens, pos, variables, outputLines, askInput, functions)
            if error:
                return error
        pos += 1  # buhbye

    pos, signal, error = codeBlock(tokens, pos, variables, outputLines, askInput, functions, [])
    if error:
        return error

    # a gtfo or found yr that is not inside a loop, switch, or function
    if signal == "BREAK":
        return semanticError(tokens, pos - 1, "GTFO is only allowed inside a loop, switch, or function")
    if signal == "RETURN":
        return semanticError(tokens, pos - 1, "FOUND YR is only allowed inside a function")
    pos += 1  # kthxbye
    if pos < len(tokens):
        return semanticError(tokens, pos, "Functions outside HAI and KTHXBYE are not supported yet")
    return None


def truncDivide(left, right):
    # divide two integers and cut the result toward zero
    quotient = abs(left) // abs(right)
    if (left < 0) != (right < 0):
        quotient = -quotient
    return quotient


def boolean(operator, left, right):
    # operands that are not TROOFs are cast first
    left = toTroof(left)
    right = toTroof(right)
    if operator == "BOTH OF":
        return left and right
    if operator == "EITHER OF":
        return left or right
    return left != right


def isEqual(left, right):
    # no typecasting in comparisons, so different types are never equal
    if getType(left) != getType(right):
        return False
    return left == right


def arithmetic(operator, left, right, tokens, pos):
    # both operands become numbers first
    left, error = toNumeric(left, tokens, pos)
    if error:
        return None, error
    right, error = toNumeric(right, tokens, pos)
    if error:
        return None, error

    # the result is a NUMBAR if at least one operand is a NUMBAR
    if type(left) is float or type(right) is float:
        left, error = toFloat(left, tokens, pos)
        if error:
            return None, error
        right, error = toFloat(right, tokens, pos)
        if error:
            return None, error

    if operator == "SUM OF":
        result = left + right
    elif operator == "DIFF OF":
        result = left - right
    elif operator == "PRODUKT OF":
        result = left * right
    elif operator == "QUOSHUNT OF":
        if right == 0:
            return None, semanticError(tokens, pos, "Cannot divide by zero")
        if type(left) is float:
            result = left / right
        else:
            result = truncDivide(left, right)
    elif operator == "MOD OF":
        if right == 0:
            return None, semanticError(tokens, pos, "Cannot get the modulo of zero")
        if type(left) is float:
            result = mathLib.fmod(left, right)
        else:
            result = left - truncDivide(left, right) * right
    elif operator == "BIGGR OF":
        result = max(left, right)
    else:
        result = min(left, right)

    if type(result) is float and not mathLib.isfinite(result):
        return None, semanticError(tokens, pos, "NUMBAR result is too large")
    return result, None


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