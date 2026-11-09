class NotSpecified(Exception):
    def __init__(self, question: str):
        super().__init__(question)
        self.question = question
