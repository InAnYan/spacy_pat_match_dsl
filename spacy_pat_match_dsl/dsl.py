from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Callable


class PatternsGrammar:
    def generate_patterns(self) -> List[Dict]:
        return [{'label': entity, 'pattern': pattern}
                for entity in filter(lambda a: a.isupper(), dir(self))
                for pattern in getattr(self, entity).get_patterns()]


Pattern = List[Dict]


class PatternGenerator(ABC):
    @abstractmethod
    def get_patterns(self) -> List[Pattern]:
        pass

    def __or__(self, other: PatternGenerator) -> PatternGenerator:
        return Or(self, other)

    def __add__(self, other: PatternGenerator) -> PatternGenerator:
        return And(self, other)


class Or(PatternGenerator):
    a: PatternGenerator
    b: PatternGenerator

    def __init__(self, a: PatternGenerator, b: PatternGenerator):
        self.a, self.b = a, b

    def get_patterns(self) -> List[Pattern]:
        return self.a.get_patterns() + self.b.get_patterns()


class And(PatternGenerator):
    a: PatternGenerator
    b: PatternGenerator

    def __init__(self, a: PatternGenerator, b: PatternGenerator):
        self.a, self.b = a, b

    def get_patterns(self) -> List[Pattern]:
        return [pa + pb for pa in self.a.get_patterns() for pb in self.b.get_patterns()]


class Token(PatternGenerator):
    dictionary: Dict

    def __init__(self, dictionary: Dict):
        self.dictionary = dictionary

    def get_patterns(self) -> List[Pattern]:
        return [[self.dictionary]]


class Optional(PatternGenerator):
    x: PatternGenerator

    def __init__(self, x: PatternGenerator):
        self.x = x

    def get_patterns(self) -> List[Pattern]:
        return self.x.get_patterns() + [[]]


def token_dict(k: str) -> Callable[[str], Token]:
    return lambda v: Token({k: v})


lower = token_dict('LOWER')
pos = token_dict('POS')
lemma = token_dict('LEMMA')

"""
class Child(PatternsGrammar):
    unit_names = lower('meter') | lower('second')
    modifier = lower('cubic') | lower('square')
    single_unit = Optional(modifier) + unit_names
    compound_unit = single_unit + lower('per') + single_unit
    UNIT = single_unit | compound_unit
    QUANTITY = pos('NUM') + UNIT
    single_terms = lower('speed') | lower('distance')
    compound_terms = lower('ampere') + lower('force') | lower('wave') + lower('propagation')
    TERM = single_terms | compound_terms
    question_words = lower('what') | lower('calculate')
    UNKNOWN = question_words + TERM
    positive_change_words = lemma('increase')
    negative_change_words = lemma('decrease') | lemma('reduce')
    change_pattern = lower('by') + Optional(lower('factor')) + Optional(lower('of')) + pos('NUM')
    POS_CHANGE = positive_change_words + change_pattern
    NEG_CHANGE = negative_change_words + change_pattern
    CHANGE_QUESTION = positive_change_words | negative_change_words | lower('change')
    special_unknown_words = lower('fast') | lower('far')
    SPECIAL_UNKNOWN = lower('how') + special_unknown_words
    COMPARISON = lower('greater') | lower('slower')


x = Child()
"""

"""
import spacy
from spacy import displacy
from spacy.matcher import Matcher

nlp = spacy.load('en_core_web_sm')
nlp.remove_pipe('ner')
ruler = nlp.add_pipe('entity_ruler')

matcher = Matcher(nlp.vocab)
for d in x.generate_patterns():
    matcher.add(d['label'], [d['pattern']])

ruler.add_patterns(x.generate_patterns())

doc = nlp('123 meter per cubic second. How far? speed is increase factor of 2')

displacy.serve(doc, style='ent')
"""
