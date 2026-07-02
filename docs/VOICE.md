# Voice guide (commits, comments, docs)

How I want git messages, code comments, and markdown to sound. Chill, young, human. Not corporate, not AI filler. Still respectful.

For Cursor/Claude when touching this repo.

---

## Core rules

- Capitalize the first letter of sentences. Proper nouns normal.
- No em dashes. Commas, periods, parentheses instead.
- No "leveraging," "utilizing," "robust," "seamless," "streamlined."
- No "it's worth noting," "this ensures," "delve into."
- Say what changed and why if it's not obvious. Short is fine.

---

## Git commits

Lowercase type prefix, sentence-case description. One-line why when needed.

Good:
```
fix(pages): redirect github pages to /web/
root was 404ing without it

feat(bracket): per-match advance % on the dashboard
sim was pairing winners wrong before this
```

Bad:
```
Updated files
Refactored the codebase for better performance and scalability
feat: Implemented the new authentication flow utilizing JWT
```

---

## Code comments

WHY not WHAT. Lowercase, conversational, 1-2 lines. Honest about debt.

Good:
```python
# simulate.py uses STRENGTH_SCALE, not ELO_SCALE, or every match looks 50/50
# keep last strength on eliminated teams for backtest
```

Bad:
```python
# This function calculates the score
# TODO: fix later
```

---

## Docs

Plain English. Short paragraphs. First person when it's me writing. Okay to say "probably" or "roughly" when true.

---

## Stuff I'd never write

- "It's worth noting that..."
- "This ensures that..."
- "Leveraging the power of..."
- Three-line comments on obvious one-liners
