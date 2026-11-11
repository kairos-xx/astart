from _typeshed import Incomplete
from antlr4.atn.ATN import ATN as ATN
from antlr4.atn.ATNState import ATNState as ATNState
from antlr4.atn.ATNState import LoopEndState as LoopEndState
from antlr4.atn.ATNState import StarLoopEntryState as StarLoopEntryState
from antlr4.atn.ParserATNSimulator import (
    ParserATNSimulator as ParserATNSimulator,
)
from antlr4.atn.Transition import Transition as Transition
from antlr4.BufferedTokenStream import TokenStream as TokenStream
from antlr4.dfa.DFA import DFA as DFA
from antlr4.error.Errors import (
    FailedPredicateException as FailedPredicateException,
)
from antlr4.error.Errors import (
    RecognitionException as RecognitionException,
)
from antlr4.error.Errors import (
    UnsupportedOperationException as UnsupportedOperationException,
)
from antlr4.Lexer import Lexer as Lexer
from antlr4.Parser import Parser as Parser
from antlr4.ParserRuleContext import (
    InterpreterRuleContext as InterpreterRuleContext,
)
from antlr4.ParserRuleContext import ParserRuleContext as ParserRuleContext
from antlr4.PredictionContext import (
    PredictionContextCache as PredictionContextCache,
)
from antlr4.Token import Token as Token

class ParserInterpreter(Parser):
    __slots__ = (
        "_parentContextStack",
        "atn",
        "decisionToDFA",
        "grammarFileName",
        "pushRecursionContextStates",
        "ruleNames",
        "sharedContextCache",
        "tokenNames",
    )
    grammarFileName: str
    atn: ATN
    tokenNames: list[Incomplete]
    ruleNames: list[str]
    decisionToDFA: list[DFA]
    sharedContextCache: PredictionContextCache
    pushRecursionContextStates: set[int]
    def __init__(
        self,
        grammarFileName: str,
        tokenNames: list[str],
        ruleNames: list[str],
        atn: ATN,
        input: TokenStream,
    ) -> None: ...
    state: int
    def parse(self, startRuleIndex: int) -> ParserRuleContext | None: ...
    def enterRecursionRule(
        self,
        localctx: ParserRuleContext,
        state: int,
        ruleIndex: int,
        precedence: int,
    ) -> None: ...
    def getATNState(self) -> ATNState: ...
    def visitState(self, p: ATNState) -> None: ...
    def visitRuleStopState(self, p: ATNState) -> None: ...
