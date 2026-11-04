class Interpreter:
    def __init__(self, tokens, output, askInput, onUpdate):
        self.tokens = tokens
        self.output = output
        self.askInput = askInput
        self.onUpdate = onUpdate
        self.variables = {"IT": None}

    def run(self):
        pass