import spacy
from spacy import displacy

from src.spacy_pat_match_dsl.dsl import PatternsGrammar, lower, pos, Token


# To create matchers create a class that inherits from `PatternsGrammar`.
class Example(PatternsGrammar):
    # All pattern matching fragments and entities are written as variable definitions inside a class.

    # Variables that are in uppercase are entities and exported in patterns.
    # All other variable names are fragments, they won't be recognized, but they can be used as fragments
    # of entity patterns.

    # To match a token (as a dictionary) instantiate a `Token` class with your dictionary.
    some_token = Token({'LOWER': 'text'})
    # For common tokens there are builtin functions like `lower`, `pos` and `lemma`.
    another_token = lower('text')

    # To make an alteration of patterns use `|` (`or`) operator.
    single_unit = lower('meter') | lower('second') | lower('kilometer') | lower('meter') | lower('kilometers')

    # To specify a sequence use `+` operator.
    # As you can see you can combine other patterns besides tokens in a pattern.
    compound_unit = single_unit + lower('per') + single_unit

    UNIT = single_unit | compound_unit
    QUANTITY = pos('NUM') + UNIT

    # Do not use recursion.
    # And probably you can't do it, because there is no way to create a forward reference to some rule.


# To use the grammar instantiate a class.
example = Example()

nlp = spacy.load('en_core_web_sm')
nlp.remove_pipe('ner')
ruler = nlp.add_pipe('entity_ruler')
# Look at the `PatternsGrammar` documentation for available methods.
ruler.add_patterns(example.generate_patterns_for_ruler())

doc = nlp('Which speed is bigger: 10 kilometers per hour or 10 meter per second? Just a unit: meter.')

# The library can also generate colors for your entities.
displacy.serve(doc, style='ent', auto_select_port=True, options={'colors': example.generate_colors()})
