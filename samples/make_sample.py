"""Generate a Japanese lesson screenshot for manual testing."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
LINES = [
    "第3課　わたしの一日",
    "",
    "毎朝六時に起きます。",
    "朝ごはんを食べてから、学校へ行きます。",
    "授業は八時半に始まります。",
    "昼ごはんは友だちと食べます。",
    "放課後、図書館で日本語を勉強します。",
    "夜十一時ごろ寝ます。",
    "",
    "文法：〜てから（after doing ~）",
    "　例：手を洗ってから、ごはんを食べます。",
]


def main(out: Path = Path(__file__).with_name("japanese_lesson.png")) -> None:
    image = Image.new("RGB", (900, 620), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(FONT, 38)
    body_font = ImageFont.truetype(FONT, 30)
    y = 40
    for index, line in enumerate(LINES):
        font = title_font if index == 0 else body_font
        draw.text((50, y), line, font=font, fill="black")
        y += 52 if index == 0 else 44
    image.save(out)
    print(out)


if __name__ == "__main__":
    main()
