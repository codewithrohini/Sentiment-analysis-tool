

import re
from flask import Flask, render_template, request, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# ----------------------------------------------------------------------
# Lightweight emotion lexicon. VADER gives us polarity (pos/neg/neu) but
# not *which* emotion is driving it, so we layer a small keyword lexicon
# on top to surface joy / frustration / trust / hesitation.
# ----------------------------------------------------------------------
EMOTION_LEXICON = {
    "joy": [
        "love", "great", "awesome", "amazing", "happy", "delight", "delighted",
        "fantastic", "excellent", "wonderful", "thrilled", "perfect", "best",
        "enjoy", "enjoyed", "glad", "pleased", "excited", "impressed", "smooth",
    ],
    "frustration": [
        "annoying", "frustrated", "frustrating", "hate", "broken", "bug",
        "crash", "crashes", "slow", "terrible", "awful", "worst", "angry",
        "ridiculous", "useless", "disappointed", "disappointing", "drives me crazy",
        "ugh", "stuck", "fail", "failed", "failure", "lag", "laggy",
    ],
    "trust": [
        "reliable", "trust", "trusted", "confident", "consistent", "secure",
        "dependable", "solid", "stable", "honest", "transparent", "support",
        "helpful", "responsive", "recommend",
    ],
    "hesitation": [
        "maybe", "unsure", "confusing", "confused", "not sure", "hesitant",
        "worried", "concerned", "doubt", "doubtful", "unclear", "hmm",
        "but", "although", "however", "wish", "could be better",
    ],
}

WORD_RE = re.compile(r"[A-Za-z']+")


def detect_emotions(text_lower):
    """Score each emotion by counting lexicon hits, return ranked list."""
    scores = {}
    for emotion, words in EMOTION_LEXICON.items():
        hits = 0
        for phrase in words:
            hits += text_lower.count(phrase)
        if hits:
            scores[emotion] = hits

    if not scores:
        return [{"emotion": "neutral", "strength": 1.0}]

    total = sum(scores.values())
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {"emotion": name, "strength": round(count / total, 2)}
        for name, count in ranked
    ]


def extract_signal_words(raw_text):
    """
    Walk every word in the text, score it with VADER's lexicon, and
    return the words that actually carry polarity, color-coded.
    """
    lexicon = analyzer.lexicon
    seen = set()
    signals = []

    for match in WORD_RE.finditer(raw_text):
        word = match.group(0)
        key = word.lower()
        if key in seen:
            continue
        score = lexicon.get(key)
        if score is None or abs(score) < 0.5:
            continue
        seen.add(key)
        signals.append(
            {
                "word": word,
                "score": score,
                "polarity": "positive" if score > 0 else "negative",
            }
        )

    signals.sort(key=lambda s: abs(s["score"]), reverse=True)
    return signals[:12]


def overall_verdict(compound):
    if compound >= 0.5:
        return "Strongly positive"
    if compound >= 0.05:
        return "Leaning positive"
    if compound <= -0.5:
        return "Strongly negative"
    if compound <= -0.05:
        return "Leaning negative"
    return "Neutral / mixed"


def confidence_from(scores):
    """
    Confidence = how decisively polarized the text is.
    A compound score near ±1 with low neutral mass -> high confidence.
    """
    decisiveness = abs(scores["compound"])
    low_neutral_bonus = (1 - scores["neu"]) * 0.4
    confidence = min(1.0, decisiveness * 0.7 + low_neutral_bonus + 0.15)
    return round(confidence * 100)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Please paste some text to analyze."}), 400
    if len(text) > 5000:
        return jsonify({"error": "Please keep text under 5,000 characters."}), 400

    scores = analyzer.polarity_scores(text)
    emotions = detect_emotions(text.lower())
    signals = extract_signal_words(text)

    return jsonify(
        {
            "verdict": overall_verdict(scores["compound"]),
            "confidence": confidence_from(scores),
            "polarity": {
                "positive": round(scores["pos"] * 100),
                "neutral": round(scores["neu"] * 100),
                "negative": round(scores["neg"] * 100),
                "compound": round(scores["compound"], 3),
            },
            "emotions": emotions,
            "signals": signals,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)