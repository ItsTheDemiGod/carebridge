"""Phase 6c-2 strings: header menu button. id -> (en, ta, hi). Drafts for ta/hi."""
STRINGS: dict[str, tuple[str, str, str]] = {
    "ui.nav.menu": ("Menu", "பட்டியல்", "मेन्यू"),
}
# Compact nav labels for the one-row desktop header. English and Hindi repeat the existing words; Tamil is shorter so the row fits.
STRINGS.update({
    "ui.nav.how_c": ("How it works", "செயல்முறை", "यह कैसे काम करता है"),
    "ui.nav.docs_c": ("Your documents", "ஆவணங்கள்", "आपके दस्तावेज़"),
    "ui.nav.start_c": ("Start", "தொடக்கம்", "शुरू करें"),
})
