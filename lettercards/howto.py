"""Shared 'Using the cards' guidance.

Single source of truth: the PDF how-to page is drawn from these strings, and a
test asserts the README's "Using the cards" section mirrors them verbatim — so
the printed guidance and the README can't drift.
"""

TITLE = "Using the cards"

INTRO = ("Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive "
         "toddlers. The deck grows with the child; don't use all of it at once. Words and "
         "letters can grow together from the very start: a child who loves a picture card "
         "can just as happily notice the colored letter on it, often well into the second "
         "year. You don't have to wait for a \"right age\" — recognising letters isn't "
         "gated behind one; it's blending them into words that usually comes later. So the "
         "ages below are the roughest of guides. Follow the child, not the number.")

# (stage, indicative ages, what to do). The stages overlap and are led by the
# child's interest — they are not gates to clear in order.
STAGES = [
    ("Naming", "from ~1",
     "As soon as the child points at and names pictures — often early in the second year — "
     "start here. Show a card, say the word, let the child point and name. A handful at a "
     "time, led by the child's interest. The printed word is for you; the colored first "
     "letter is right there for the child to notice whenever she's curious about it."),
    ("First sounds", "from ~2",
     "Sound games with the picture cards: “b-b-b… bal!” The colored first letter shows what "
     "to stress. Sort cards by first sound — all cards for a letter share their band color."),
    ("Letters", "child-led, alongside words",
     "Bring in the letter-family cards and match picture cards to their letter. Many "
     "children are keen on letters as young toddlers — if she's already pointing at them, "
     "follow her lead rather than holding the cards back for a later age."),
    ("First words", "once a few sounds are known",
     "When the child knows a handful of letter sounds, start blending them: say the sounds "
     "close together and let them melt into the word — “mmm-aaa-nnn… man”. Slide a finger "
     "under the letters as you go. Short, sound-it-out words first, with the picture there "
     "to confirm the answer. This is the bridge from single letters to reading."),
]

# (heading, body) — two things worth knowing about how letters behave, so they
# don't ambush you mid-game.
NOTES_TITLE = "Two things about letters"
NOTES = [
    ("A letter wears different clothes",
     "The same letter looks different as a capital and a small letter, in print and in "
     "handwriting — A and a are one letter. Children learn this by seeing it, not by being "
     "told: point out the same letter in its many forms, on the card, on a sign, in a name. "
     "The specimen row on each letter-family card is built for exactly this — one letter, "
     "different clothes."),
    ("A letter can make more than one sound",
     "Some letters aren't loyal to one sound. Vowels come short and long (the a in “appel” "
     "versus “maan”); a c can sound like a k or an s. Teach the sound in the card's word "
     "first — one letter, one sound — and mention the others only later, as “this one can "
     "also say…”. Don't crowd the first sound with its exceptions."),
]

OUTRO = ("Say letter sounds, not names — “mmm”, not “em”. The word list "
         "is curated for this: the first letter is the first sound.")
