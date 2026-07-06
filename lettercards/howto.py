"""Shared 'Using the cards' guidance.

Single source of truth: the PDF how-to page is drawn from these strings, and a
test asserts the README's "Using the cards" section mirrors them verbatim — so
the printed guidance and the README can't drift.

Deliberately minimal (v2): a practical page, not a pedagogy. The staged
letter-learning progression is frozen for v3 — see issue #26.
"""

TITLE = "Using the cards"

INTRO = ("The deck grows with the child — don't use all of it at once. Show a card, say the "
         "word, and let the child point and name it; a handful of cards at a time, led by "
         "the child's interest. Keep it playful, and stop before it becomes a drill.")

OUTRO = ("Say letter sounds, not names — “mmm”, not “em”. The colored first letter is that "
         "sound — the first sound of the word — and every card for a letter shares its band "
         "color, so the cards sort into families.")
