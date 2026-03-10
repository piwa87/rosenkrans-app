"""Shared localization settings for the rosary tracker."""

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict

DEFAULT_LANGUAGE = "en"

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "da": "Dansk",
}

UI_TRANSLATIONS = {
    "en": {
        "page_title": "Rosary Progress Tracker",
        "title": "🙏 Rosary Progress Tracker",
        "language_label": "Language",
        "svg_label": "Rosary bead tracker",
        "svg_title": "Rosary bead progress tracker",
        "waiting": "🙏 Waiting for prayer…",
        "current_bead": "Current bead",
        "our_father": "Our Father",
        "hail_mary": "Hail Mary",
        "completed": "Completed",
        "decade": "Decade {number}",
        "status_our_father": "✝️  Decade {decade} — Our Father",
        "status_hail_mary": "📿 Decade {decade} — Hail Mary {bead} / 10",
        "status_glory_be": "✨ Decade {decade} — Glory Be ✓",
        "status_complete": "🎉 Rosary Complete! God bless you.",
        "bead_count": "Bead {bead} of 10",
    },
    "da": {
        "page_title": "Rosenkrans-fremskridt",
        "title": "🙏 Rosenkrans-fremskridt",
        "language_label": "Sprog",
        "svg_label": "Oversigt over rosenkransens perler",
        "svg_title": "Rosenkransens perleoversigt",
        "waiting": "🙏 Venter på bøn…",
        "current_bead": "Nuværende perle",
        "our_father": "Fadervor",
        "hail_mary": "Hil dig, Maria",
        "completed": "Fuldført",
        "decade": "Dekade {number}",
        "status_our_father": "✝️  Dekade {decade} — Fadervor",
        "status_hail_mary": "📿 Dekade {decade} — Hil dig, Maria {bead} / 10",
        "status_glory_be": "✨ Dekade {decade} — Ære være Faderen ✓",
        "status_complete": "🎉 Rosenkransen er fuldført! Gud velsigne dig.",
        "bead_count": "Perle {bead} af 10",
    },
}


def normalize_language(language: str | None) -> str:
    """Return a supported language code, falling back to English."""
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


@dataclass
class LanguageSettings:
    """Thread-safe shared language preference."""

    language: str = DEFAULT_LANGUAGE
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def get_language(self) -> str:
        with self._lock:
            return normalize_language(self.language)

    def set_language(self, language: str) -> str:
        normalized = normalize_language(language)
        with self._lock:
            self.language = normalized
            return self.language
