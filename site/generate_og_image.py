"""Generate OG image (1200x630) with chart and title overlay."""
from PIL import Image, ImageDraw, ImageFont
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_PATH = os.path.join(SCRIPT_DIR, "..", "paper", "figures", "pass_fail_by_source.png")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "og-image.png")

WIDTH, HEIGHT = 1200, 630
BG_COLOR = (15, 23, 42)  # dark slate
ACCENT = (59, 130, 246)  # blue
TEXT_COLOR = (255, 255, 255)
SUBTEXT_COLOR = (148, 163, 184)  # slate-400

img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

# Load chart and place on right side
chart = Image.open(CHART_PATH)
# Scale chart to fit right portion (roughly 55% of width, with padding)
chart_area_w = 640
chart_area_h = 480
chart.thumbnail((chart_area_w, chart_area_h), Image.LANCZOS)
# Center chart in right half
chart_x = WIDTH - chart.width - 40
chart_y = (HEIGHT - chart.height) // 2
# Add white background behind chart for readability
chart_bg = Image.new("RGB", (chart.width + 20, chart.height + 20), (255, 255, 255))
img.paste(chart_bg, (chart_x - 10, chart_y - 10))
img.paste(chart, (chart_x, chart_y))

# Text on left side
left_margin = 50
max_text_width = 480

# Try to load a good font, fall back to default
def load_font(size, bold=False):
    # Try common macOS system fonts
    candidates = [
        "/System/Library/Fonts/SFPro-Bold.otf" if bold else "/System/Library/Fonts/SFPro-Regular.otf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

font_title = load_font(36, bold=True)
font_subtitle = load_font(18)
font_stats = load_font(44, bold=True)
font_stat_label = load_font(16)

# Title
draw.text((left_margin, 40), "Agent Skill", fill=TEXT_COLOR, font=font_title)
draw.text((left_margin, 82), "Analysis", fill=TEXT_COLOR, font=font_title)

# Subtitle
draw.text((left_margin, 135), "673 skills from 41 repositories", fill=SUBTEXT_COLOR, font=font_subtitle)

# Accent line
draw.rectangle([left_margin, 170, left_margin + 60, 174], fill=ACCENT)

# Key stats
stats = [
    ("22%", "fail validation"),
    ("52%", "token waste"),
    ("3.12", "mean novelty (of 5)"),
]

y = 200
for value, label in stats:
    draw.text((left_margin, y), value, fill=ACCENT, font=font_stats)
    # Get width of value text to place label next to it
    bbox = draw.textbbox((0, 0), value, font=font_stats)
    val_width = bbox[2] - bbox[0]
    draw.text((left_margin + val_width + 12, y + 16), label, fill=SUBTEXT_COLOR, font=font_stat_label)
    y += 65

# Bottom tagline
draw.text((left_margin, HEIGHT - 60), "agentskillreport.com", fill=SUBTEXT_COLOR, font=font_subtitle)

# Subtle border
draw.rectangle([0, 0, WIDTH - 1, HEIGHT - 1], outline=(30, 41, 59), width=1)

img.save(OUTPUT_PATH, "PNG", optimize=True)
print(f"Saved {OUTPUT_PATH} ({WIDTH}x{HEIGHT})")
