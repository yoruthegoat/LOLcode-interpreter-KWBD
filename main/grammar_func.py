# CMSC 124 milestone 1

import re

# keyword and its classification
KEYWORD_TYPES = {
    "HAI": "Code Delimiter",
    "KTHXBYE": "Code Delimiter",
    "WAZZUP": "Variable List Delimiter",
    "BUHBYE": "Variable List Delimiter",
    "BTW": "Comment Delimiter",
    "OBTW": "Comment Delimiter",
    "TLDR": "Comment Delimiter",
    "I HAS A": "Variable Declaration",
    "ITZ": "Variable Assignment",
    "R": "Assignment Operator",
    "AN": "Operand Separator",
    "SUM OF": "Addition Operator",
    "DIFF OF": "Subtraction Operator",
    "PRODUKT OF": "Multiplication Operator",
    "QUOSHUNT OF": "Division Operator",
    "MOD OF": "Modulo Operator",
    "BIGGR OF": "Max Operator",
    "SMALLR OF": "Min Operator",
    "BOTH OF": "AND Operator",
    "EITHER OF": "OR Operator",
    "WON OF": "XOR Operator",
    "NOT": "NOT Operator",
    "ANY OF": "Infinite Arity OR",
    "ALL OF": "Infinite Arity AND",
    "BOTH SAEM": "Equality Operator",
    "DIFFRINT": "Inequality Operator",
    "SMOOSH": "Concatenation Keyword",
    "MAEK": "Typecasting Keyword",
    "A": "Typecasting Keyword",
    "IS NOW A": "Typecasting Keyword",
    "VISIBLE": "Output Keyword",
    "GIMMEH": "Input Keyword",
    "O RLY?": "If-Then Delimiter",
    "YA RLY": "If Clause",
    "MEBBE": "Else-If Clause",
    "NO WAI": "Else Clause",
    "OIC": "Conditional Delimiter",
    "WTF?": "Switch Delimiter",
    "OMG": "Case Keyword",
    "OMGWTF": "Default Case Keyword",
    "IM IN YR": "Loop Delimiter",
    "IM OUTTA YR": "Loop Delimiter",
    "UPPIN": "Increment Keyword",
    "NERFIN": "Decrement Keyword",
    "YR": "Parameter Delimiter",
    "TIL": "Loop Condition",
    "WILE": "Loop Condition",
    "HOW IZ I": "Function Delimiter",
    "IF U SAY SO": "Function Delimiter",
    "GTFO": "Break Keyword",
    "FOUND YR": "Return Keyword",
    "I IZ": "Function Call",
    "MKAY": "Infinite Arity Delimiter"
}
# check longer keywords first
KEYWORDS = sorted(KEYWORD_TYPES, key=len, reverse=True)

# identifiers that name a function or loop instead of a variable
IDENTIFIER_AFTER = {
    "HOW IZ I": "Function Identifier",
    "I IZ": "Function Identifier",
    "IM IN YR": "Loop Identifier",
    "IM OUTTA YR": "Loop Identifier"
}


def classify(word):
    # fullmatch checks the whole word, so 12abc will not match a number
    if re.fullmatch(r"WIN|FAIL", word):
        return "Literal"
    if re.fullmatch(r"NOOB|NUMBR|NUMBAR|YARN|TROOF", word):
        return "Type Literal"

    # optional minus sign followed by digits
    if re.fullmatch(r"-?[0-9]+", word):
        return "Literal"

    # decimal point needs at least one digit after it
    if re.fullmatch(r"-?[0-9]*\.[0-9]+", word):
        return "Literal"

    # starts with a letter, then letters, digits, or underscores
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", word):
        return "Variable Identifier"
    return "Invalid"


def scan(source):
    tokens=[]
    errors = []
    commentLine= 0
    lineNum = 0

    for line in source.splitlines():
        lineNum+=1
        i=0
        while i < len(line):
            if line[i].isspace():
                i += 1
                continue

            # skip comment body until TLDR
            if commentLine != 0:
                if line[i:].split()[0] == "TLDR":
                    tokens.append(("TLDR", KEYWORD_TYPES["TLDR"], lineNum))
                    commentLine = 0
                break

            start= i

            # read string, keeping the spaces inside
            if line[i] == '"':
                i += 1
                while i < len(line) and line[i] != '"':
                    i += 1
                if i == len(line):
                    errors.append((lineNum, "Missing closing quote."))
                    break
                i += 1
                # quotes are delimiters, the text between them is the literal
                tokens.append(('"', "String Delimiter", lineNum))
                tokens.append((line[start+1:i-1], "Literal", lineNum))
                tokens.append(('"', "String Delimiter", lineNum))
                continue

            # check keywords
            keyword = ""
            for candidate in KEYWORDS:
                end = i+len(candidate)
                if line[i:end] == candidate:
                    if end == len(line) or line[end].isspace() or line[end] in '\"+':
                        keyword = candidate
                        break

            if keyword != "":
                tokens.append((keyword, KEYWORD_TYPES[keyword], lineNum))
                i+= len(keyword)
                if keyword == "BTW":
                    break
                if keyword == "OBTW":
                    if line[:start].strip() != "":
                        errors.append((lineNum, "OBTW must start on its own line."))
                    commentLine = lineNum
                    break
                if keyword == "TLDR":
                    errors.append((lineNum, "TLDR without OBTW."))
                continue

            if line[i] == "+":
                tokens.append(("+", "Output Separator", lineNum))
                i += 1
                continue

            # read word and check its type
            while i < len(line):
                if line[i].isspace() or line[i] in '\"+':
                    break
                i += 1
            word=line[start:i]
            tokenType= classify(word)
            if tokenType == "Invalid":
                errors.append((lineNum, "Invalid lexeme: " + word))
            else:
                # name right after HOW IZ I, I IZ, or IM IN YR
                if tokenType == "Variable Identifier" and tokens and tokens[-1][2] == lineNum:
                    tokenType = IDENTIFIER_AFTER.get(tokens[-1][0], tokenType)
                tokens.append((word, tokenType, lineNum))

    if commentLine != 0:
        errors.append((commentLine, "Missing TLDR for block comment."))
    return tokens, errors


def main():
    # open file
    fileName = input("Enter the .lol file path: ").strip()
    try:
        with open(fileName, "r", encoding="utf-8-sig") as fp:
            source = fp.read()
    except (OSError, UnicodeError) as error:
        print("Cannot read file:", error)
        return

    # get tokens
    tokens,errors = scan(source)


    # print results
    print(f"\n{'Line':<6}{'Classification':<28}Lexeme")
    print("-" * 70)
    for word, tokenType, line in tokens:
        print(f"{line:<6}{tokenType:<28}{word}")
    for line, message in errors:
        print("Error on line", str(line) + ":", message)
    print("\nTokens:", len(tokens), "| Lexical errors:", len(errors))


if __name__ == "__main__":
    main()
