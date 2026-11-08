"""Provided with the specification. Do not modify this file."""


class NotSpecified(Exception):
    """May be raised by a function in this workspace. `question` is a short human-readable question."""

    def __init__(self, question: str):
        super().__init__(question)
        self.question = question
