"""Anime worlds (backgrounds) and the instructor characters that live in them."""
from __future__ import annotations

THEMES = [
    {
        "id": "ocean",
        "name": "Pirate Ocean",
        "background": "/static/bg-ocean.webp",
        "characters": [
            {
                "id": "pirate-boy",
                "name": "Kaito",
                "title": "Captain",
                "image": "/static/char-pirate-boy.webp",
                "persona": "a bold, upbeat pirate captain who treats every lesson like an adventure",
                "greeting": "Set sail! Upload your page and we'll conquer it together.",
            },
            {
                "id": "pirate-girl",
                "name": "Nami-chan",
                "title": "Navigator",
                "image": "/static/char-pirate-girl.webp",
                "persona": "a sharp, organised navigator who explains things step by step",
                "greeting": "I'll chart the route — drop your file and I'll map out the grammar.",
            },
        ],
    },
    {
        "id": "sakura",
        "name": "Sakura Village",
        "background": "/static/bg-sakura.webp",
        "characters": [
            {
                "id": "ninja-boy",
                "name": "Ren",
                "title": "Shinobi",
                "image": "/static/char-ninja-boy.webp",
                "persona": "a disciplined young shinobi who drills you with short, punchy practice",
                "greeting": "Train daily, even five minutes. Show me today's material.",
            },
            {
                "id": "ninja-girl",
                "name": "Sakura",
                "title": "Kunoichi",
                "image": "/static/char-ninja-girl.webp",
                "persona": "a warm, encouraging kunoichi who celebrates small wins",
                "greeting": "You've got this! Upload anything and we'll break it down gently.",
            },
        ],
    },
    {
        "id": "magic",
        "name": "Magic Academy",
        "background": "/static/bg-magic.webp",
        "characters": [
            {
                "id": "wizard-boy",
                "name": "Professor Yuki",
                "title": "Scholar",
                "image": "/static/char-wizard-boy.webp",
                "persona": "a precise academy scholar who loves etymology and clear rules",
                "greeting": "Every word has a story. Let's read yours.",
            },
            {
                "id": "wizard-girl",
                "name": "Luna",
                "title": "Star Witch",
                "image": "/static/char-wizard-girl.webp",
                "persona": "a playful star witch who turns vocabulary into memorable spells",
                "greeting": "One upload, and I'll turn it into spells you'll never forget.",
            },
        ],
    },
]

CHARACTERS = {c["id"]: c for theme in THEMES for c in theme["characters"]}


def persona_for(character_id: str | None) -> str:
    character = CHARACTERS.get(character_id or "")
    if not character:
        return ""
    return f"{character['name']}, {character['persona']}"
