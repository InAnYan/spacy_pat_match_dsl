from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Tuple, Iterable

Pattern = List[Dict]
"""A spaCy pattern"""


class PatternGenerator(ABC):
    """A class used to represent parts of grammar."""

    @abstractmethod
    def generate_patterns(self) -> List[Pattern]:
        """Return list of patterns for a part of grammar.

        Returns
        -------
        List[Pattern]
        """
        pass

    def __or__(self, other: PatternGenerator) -> PatternGenerator:
        """An overload for `or` operator.

        Parameters
        ----------
        other : PatternGenerator
            A pattern generator to combine.

        Returns
        -------
        PatternGenerator
            A new pattern generator that is an alteration of two pattern generators.
        """
        return Or(self, other)

    def __add__(self, other: PatternGenerator) -> PatternGenerator:
        """An overload for `+` operator.

        Parameters
        ----------
        other : PatternGenerator
            A pattern generator to combine.

        Returns
        -------
        PatternGenerator
            A new pattern generator that is a combination of two pattern generators.
        """
        return And(self, other)


class PatternsGrammar:
    """Parent class for all user grammars.

    Your grammar should be instantiated from this class.
    This class provides methods for generating entity patterns.
    Also, it provides a method for generating a color pallet for entities.
    """

    def generate_patterns_tuple(self) -> List[Tuple[str, List[Pattern]]]:
        """Generate a list of tuples of entities.

        Each tuple contain entity name and list of patterns for that entity.
        This method is useful when you need to add patterns to spaCy `Matcher`.

        Returns
        -------
        List[Tuple[str, List[Pattern]]
            List of entity patterns.
        """
        return [(entity, generator.generate_patterns())
                for (entity, generator) in self.enumerate_entities()]

    def generate_patterns_for_ruler(self) -> List[Dict]:
        """Generate a list of dictionary of entities.

        Each dictionary is in form: `{'label': entity, 'pattern': pattern}`,
        where entity is an entity name and pattern is a pattern for that entity.
        This method is useful when you need to add patterns to spaCy `EntityRuler`.

        Returns
        -------
        List[Tuple[str, List[Pattern]]
            List of entity patterns.
        """
        return [{'label': entity, 'pattern': pattern}
                for (entity, patterns) in self.generate_patterns_tuple()
                for pattern in patterns]

    def generate_colors(self) -> Dict:
        """Generate a color palette for exported entities.

        This method is useful when presenting the results of entity recognition with displaCy.

        Notes
        -----
        In order to use the result of this method with displaCy, you should create an options dictionary
        for displaCy and place the result in the `'colors'` key.

        Returns
        ------
        Dict
            A dictionary, key of which is an entity name and value of which is an RGB code.
        """
        palette = ["#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#f39c12", "#e74c3c", "#95a5a6"]

        res = {}
        for i, entity in enumerate(self.get_entity_names()):
            res |= {entity: palette[i % len(palette)]}
        return res

    def get_entity_names(self) -> Iterable[str]:
        """Return exported entity names.

        Returns
        -------
        List[str]
            List of entity names.
        """
        return filter(lambda a: a.isupper(), dir(self))

    def enumerate_entities(self) -> Iterable[Tuple[str, PatternGenerator]]:
        """Return a list of entity name and its pattern generator

        Analogous to builtin `enumerate` function.

        Returns
        -------
        Iterable[(str, PatternGenerator)]
            List of names and generators.
        """
        return [(entity, getattr(self, entity))
                for entity in self.get_entity_names()]

    def get_productions_names(self) -> Iterable[str]:
        """Return a list of all productions (entities and fragments).

        Returns
        -------
        Iterable[str]
            List of production names.
        """
        return [n for n in dir(self) if isinstance(getattr(self, n), PatternGenerator)]

    def enumerate_productions(self) -> Iterable[(str, PatternGenerator)]:
        """Return a list of production name and production pattern generator

        Analogous to builtin `enumerate` function.

        Returns
        -------
        Iterable[(str, PatternGenerator)]
            List of names and generators.
        """
        return [(name, getattr(self, name)) for name in self.get_productions_names()]

    def to_bnf(self) -> List[str]:
        """Generate a BNF-like form of the patterns.

        Non-terminals are wrapped in '<>'.
        Lower case form of a token is wrapped in single quotes.
        Lemma of a token is wrapped in tilda.
        A POS of a token is prefixed with @.

        Notes
        -----
        This method does not count the precedence of combination and alteration.

        Returns
        -------
        List[str]
            List of string where each string is an expansion.
        """

        return [f'<{name}> ::= {self.__make_bnf_expansion(expansion, True)}'
                for (name, expansion) in self.enumerate_productions()]

    def __make_bnf_expansion(self, x: PatternGenerator, first_expansion: bool = False) -> str:
        if not first_expansion:
            for (name, generator) in self.enumerate_productions():
                if x == generator:
                    return f'<{name}>'

        if isinstance(x, Token):
            return self.__make_bnf_token_expansion(x.dictionary)
        elif isinstance(x, Optional):
            return '[' + self.__make_bnf_expansion(x.generator) + ']'
        elif isinstance(x, Or):
            # WARNING: The method does not count the precedence of operators.
            return ' | '.join(map(lambda y: self.__make_bnf_expansion(y), x.lst))
        elif isinstance(x, And):
            return ' '.join(map(lambda y: self.__make_bnf_expansion(y), x.lst))
        else:
            raise NotImplemented()

    def __make_bnf_token_expansion(self, d: Dict) -> str:
        if len(d.keys()) == 1:
            key = list(d.keys())[0]
            value = d[key]

            if isinstance(value, Dict) and len(value.keys()) == 1 and list(value.keys())[0] == 'IN':
                return ' | '.join(map(lambda x: self.__make_bnf_token_expansion({key: x}), value['IN']))
            elif key == 'LOWER':
                return f"'{value}'"
            elif key == 'POS':
                return f"@{value}"
            elif key == 'LEMMA':
                return f"~{value}~"
            else:
                return str(d)
        else:
            return str(d)


class Or(PatternGenerator):
    """Pattern generator for alteration of pattern generators.

    You can also use the `|` overload of `PatternGenerator` to create this class.

    Attributes
    ----------
    lst : Tuple[PatternGenerator, ...]
        Tuple of combined generators.
    """

    lst: Tuple[PatternGenerator, ...]

    def __init__(self, *lst: PatternGenerator):
        """Create an alteration pattern generator.

        Parameters
        ---------
        *lst : PatternGenerator
            Pattern generators to combine.
        """

        self.lst = lst

    def generate_patterns(self) -> List[Pattern]:
        """Generate patterns of alteration.

        Basically it is just a concatenation of patterns of the supplied generators.

        Returns
        -------
        List[Pattern]
        """
        return [p
                for g in self.lst
                for p in g.generate_patterns()]


class And(PatternGenerator):
    """Pattern generator for combination of pattern generators.

    You can also use the `+` overload of `PatternGenerator` to create this class.

    Attributes
    ----------
    lst : Tuple[PatternGenerator, ...]
        Tuple of combined generators.
    """

    lst: Tuple[PatternGenerator, ...]

    def __init__(self, *lst: PatternGenerator):
        """Create a combination pattern generator.

        Parameters
        ---------
        *lst : PatternGenerator
            Pattern generators to combine.
        """

        self.lst = lst

    def generate_patterns(self) -> List[Pattern]:
        """Generate patterns of combination.

        Returns
        -------
        List[Pattern]
        """
        # :)
        return list(map(lambda x: list(itertools.chain(*x)),
                        itertools.product(*map(lambda x: x.generate_patterns(),
                                               self.lst))))


class Token(PatternGenerator):
    """A pattern generator that resembles a one spaCy token.

    Attributes
    ----------
    dictionary : Dict
        A token to match.
    """

    dictionary: Dict

    def __init__(self, dictionary: Dict):
        """Create a token pattern generator.

        Parameters
        ----------
        dictionary: Dict
            A token to match.
        """
        self.dictionary = dictionary

    def generate_patterns(self) -> List[Pattern]:
        """Generate patterns for the token.

        Basically, it is just one pattern that contains one token and that token is the supplied dictionary.

        Returns
        -------
        List[Patterns]
            Patterns for the token.
        """
        return [[self.dictionary]]


class Optional(PatternGenerator):
    """A pattern generator that creates an optional part of a grammar.

    Attributes
    ----------
    generator : PatternGenerator
        A generator to omit or not.
    """
    generator: PatternGenerator

    def __init__(self, x: PatternGenerator):
        """Create an optional part.

        Parameters
        ----------
        x : PatternGenerator
            The optional part of a grammar.
        """
        self.generator = x

    def generate_patterns(self) -> List[Pattern]:
        """Generate patterns for optional part of a grammar.

        Basically, it just returns a combination of the patterns of supplied generator and an empty list.
        A better implementation would rather utilize the `{'OP': '?'}` parameter.

        Returns
        -------
        List[Pattern]
            Patterns for optional part.
        """
        return self.generator.generate_patterns() + [[]]


def token_dict(k: str) -> Callable[[str], Token]:
    """Private function of the library that is used to create functions for often used token generators.

    Parameters
    ----------
    k : str
        A key in the token dictionary.

    Returns
    -------
    Callable[[str], Token]
        An anonymous function that accepts a string and creates a Token class with the supplied
        key and value in the dictionary.
    """
    return lambda v: Token({k: v})


lower = token_dict('LOWER')
"""A shorthand function to make tokens that match the lowercase form of a token."""

pos = token_dict('POS')
"""A shorthand function to make tokens that match the specific part of speech."""

lemma = token_dict('LEMMA')
"""A shorthand function to make tokens that match the lemma of a token."""


def token_in_list(k: str) -> Callable[[List[str]], Token]:
    """Private function of the library that is used to create functions for often used token generators.

    It makes functions value of which is `{'IN': ...}`.

    Parameters
    ----------
    k: str
        Name of the key.

    Returns
    -------
    Callable[[List[str]], Token]
        The constructor function.
    """
    return lambda lst: Token({k: {'IN': lst}})


lower_in_list = token_in_list('LOWER')
"""A shorthand function to make tokens whose lowercase form is a member of the supplied list."""

lemma_in_list = token_in_list('LEMMA')
"""A shorthand function to make tokens whose lemma is a member of the supplied list."""


def lower_in(*lst: str) -> Token:
    """A shorthand function to make tokens whose lowercase form is a member of the supplied strings."""
    return lower_in_list(list(lst))


def lemma_in(*lst: str) -> Token:
    """A shorthand function to make tokens whose lemma is a member of the supplied strings."""
    return lemma_in_list(list(lst))
