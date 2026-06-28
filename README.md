# Sentilune — AI-powered sentiment studio

A small Flask app that analyzes pasted text for sentiment, emotional tone,
confidence, and the specific words driving the result.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

## How the analysis works (app.py)

- **Polarity / confidence** — VADER (`vaderSentiment`) scores the text for
  positive / neutral / negative mass and a compound score. Confidence is
  derived from how decisive (non-neutral) that compound score is.
- **Tone & emotion** — a small hand-built lexicon (`EMOTION_LEXICON`) flags
  words tied to joy, frustration, trust, or hesitation, then ranks them by
  frequency.
- **Signal words** — every word in the input is checked against VADER's own
  lexicon; words with |score| ≥ 0.5 are returned and color-coded by polarity
  in the UI.

## Files

- `app.py` — Flask routes + all sentiment logic
- `templates/index.html` — page markup
- `static/style.css` — design system (cream / coral / maroon / olive palette)
- `static/script.js` — calls `/api/analyze` and renders the results panel
-