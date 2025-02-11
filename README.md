# A simple DSL for creating spaCy pattern matchers

```python
class Example(PatternsGrammar):
    single_unit = lower('meters') | lower('second') | lower('kilometers') | lower('hour')
    compound_unit = single_unit + lower('per') + single_unit
	
    UNIT = single_unit | compound_unit
    QUANTITY = pos('NUM') + UNIT
```

In this text:

```plain
The car is traveling at a speed of 108 kilometers per hour. Represent this speed in meters per second.
```

These entities wil be recognized:

- `108 kilometers per hour` - `QUANTITY`.
- `meters per second` - `UNIT`.

https://pypi.org/project/spacy-pat-match-dsl/

## Features

- Allows for easier constructing and extending of rule-based NER (Named Entity Recognition) systems.
- Supports many common modifiers such as: `lower` (lowercase form), `pos` (part-of-speech), `lemma` (lemmatized word).
- You can also generate BNF (Backus-Naur form) of the patterns for use in documentation or scientific papers.

## How to Run this Project

This project is a library, intended to used in other projects.

See [the example script](examples/example.py) for details on usage.

Also see documentation in [the source code](src/spacy_pat_match_dsl/dsl.py) for all capabilities of this project.

## How this Project is Implemented

This project is inspired by [lrparsing](https://pypi.org/project/lrparsing/).

- Patterns are represented via special classes.
- These classes have method `generate_patterns` which generates `spaCy`-native datastructre for NER patterns.
- `PatternGrammar` reads its own static variables and collects all the patterns.
