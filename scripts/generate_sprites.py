from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "assets" / "citizens.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

# 21 aparências: 20 habitantes iniciais e o avatar do jogador.
skins = [
    "#e9b98f", "#c98e68", "#f0c9a2", "#9b674d", "#e4ae83",
    "#d49a73", "#f1c49b", "#ad7658", "#e8b58c", "#c78d6a",
    "#f0c8a1", "#9b6a50", "#e2b18b", "#c68c68", "#f1c5a0",
    "#a66e51", "#e7b58f", "#d79d76", "#9c694e", "#edc09a",
    "#e8bd91"
]
shirts = [
    "#527da1", "#9a6d9f", "#648c67", "#b37a54", "#5f8c8e",
    "#9c765d", "#a8a06a", "#6e83aa", "#ad6f70", "#5f8d76",
    "#b18a56", "#7c6da0", "#5483a5", "#a16c52", "#6e987d",
    "#987b9e", "#b17c5d", "#6e8798", "#8d9d68", "#a46e73",
    "#d6b66e"
]
hairs = [
    "#34251f", "#241e1d", "#8a5b36", "#242020", "#b17d48",
    "#342b25", "#6e4830", "#202329", "#76503a", "#34221d",
    "#b6a16c", "#292322", "#5b382b", "#242020", "#8b6347",
    "#382923", "#c0a06a", "#29221f", "#72513a", "#30201d",
    "#3a2a24"
]
pants = ["#34414c", "#44394d", "#3e4939", "#554334", "#394b50"]
W, H = 48, 21 * 4 * 24
sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))

for person in range(21):
    skin = skins[person]
    shirt = shirts[person]
    hair = hairs[person]
    trouser = pants[person % len(pants)]
    for direction in range(4):  # frente, esquerda, direita, costas
        for frame in range(3):
            ox, oy = frame * 16, (person * 4 + direction) * 24
            d = ImageDraw.Draw(sheet)
            # Sombra e pés alternados para a animação de caminhada.
            leg_shift = (-1 if frame == 0 else 1 if frame == 2 else 0)
            d.rectangle((ox+4, oy+21, ox+11, oy+22), fill="#1b281e")
            d.rectangle((ox+5+leg_shift, oy+18, ox+7+leg_shift, oy+22), fill=trouser)
            d.rectangle((ox+9-leg_shift, oy+18, ox+11-leg_shift, oy+22), fill=trouser)
            d.rectangle((ox+4+leg_shift, oy+22, ox+7+leg_shift, oy+23), fill="#392f29")
            d.rectangle((ox+9-leg_shift, oy+22, ox+12-leg_shift, oy+23), fill="#392f29")
            # Corpo, braços e roupa.
            d.rectangle((ox+3, oy+10, ox+12, oy+18), fill=shirt)
            d.rectangle((ox+2, oy+11, ox+3, oy+17), fill=skin)
            d.rectangle((ox+12, oy+11, ox+13, oy+17), fill=skin)
            d.rectangle((ox+5, oy+11, ox+10, oy+12), fill="#ffffff")
            # Cabeça e cabelo.
            d.rectangle((ox+5, oy+3, ox+10, oy+10), fill=skin)
            d.rectangle((ox+4, oy+4, ox+5, oy+8), fill=skin)
            d.rectangle((ox+10, oy+4, ox+11, oy+8), fill=skin)
            d.rectangle((ox+4, oy+2, ox+11, oy+5), fill=hair)
            d.rectangle((ox+5, oy+1, ox+10, oy+3), fill=hair)
            if person % 4 == 1:
                d.rectangle((ox+4, oy+5, ox+5, oy+8), fill=hair)
            if person % 5 == 2:
                d.rectangle((ox+5, oy, ox+10, oy+1), fill=hair)
            # Rosto orientado.
            if direction == 0:
                d.point((ox+6, oy+7), fill="#292321")
                d.point((ox+9, oy+7), fill="#292321")
            elif direction == 1:
                d.point((ox+5, oy+7), fill="#292321")
            elif direction == 2:
                d.point((ox+10, oy+7), fill="#292321")
            # Costas: cabelo cobre parte da nuca.
            if direction == 3:
                d.rectangle((ox+5, oy+5, ox+10, oy+9), fill=hair)
            # Pequeno detalhe individual no traje.
            if person == 20:
                d.rectangle((ox+7, oy+13, ox+8, oy+15), fill="#f3df9c")

sheet.save(OUT)
print(f"Created {OUT} ({sheet.width}x{sheet.height})")

# Ícone do inicializador: personagem em primeiro plano e silhueta da cidade.
icon = Image.new("RGBA", (128, 128), "#17251c")
d = ImageDraw.Draw(icon)
d.rectangle((0, 84, 128, 127), fill="#2d4934")
for x, width, height, color in [
    (5, 27, 43, "#806b50"), (35, 24, 57, "#6b5b49"),
    (92, 29, 48, "#8d7657"), (68, 20, 35, "#536c4d")
]:
    d.rectangle((x, 84-height, x+width, 84), fill=color)
    d.rectangle((x+5, 84-height+9, x+10, 84-height+15), fill="#d7c18b")
    d.rectangle((x+16, 84-height+9, x+21, 84-height+15), fill="#d7c18b")
character = sheet.crop((16, 20 * 4 * 24, 32, 20 * 4 * 24 + 24))
character = character.resize((64, 96), Image.Resampling.NEAREST)
icon.alpha_composite(character, (32, 25))
d = ImageDraw.Draw(icon)
d.rectangle((0, 0, 127, 127), outline="#d6bd78", width=4)
icon.save(OUT.parent / "icon.png")
