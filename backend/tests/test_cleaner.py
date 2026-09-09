from app.knowledge.cleaner import TranscriptCleaner


def test_cleaner_normalizes_whitespace():
    raw = "Lenny:   Hello world!   \n\n\n\n\nRahul:    Hi Lenny!   "
    cleaned = TranscriptCleaner.clean(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Lenny: Hello world!" in cleaned
    assert "Rahul: Hi Lenny!" in cleaned


def test_cleaner_strips_sponsorship_patterns():
    raw = "Lenny: Welcome. [Ad break: visit sponsor dot com] Rahul: Here is the framework."
    cleaned = TranscriptCleaner.clean(raw)
    assert "[Ad break" not in cleaned
    assert "Rahul: Here is the framework." in cleaned


def test_cleaner_preserves_dialogue_content():
    raw = "Lenny: How did you measure PMF?\n\nRahul Vohra: With the 40% disappointed survey."
    cleaned = TranscriptCleaner.clean(raw)
    assert "Rahul Vohra: With the 40% disappointed survey." in cleaned

