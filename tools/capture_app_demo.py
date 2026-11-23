"""Capture the *running* Tkinter UI with fictional local test data.

The output is a real screenshot from Linux/Xvfb for the website, not an AI mockup.
No PCSX2, BIOS, games or copyrighted cover art are downloaded or executed.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageGrab

from ps2studio.config import AppConfig, ConfigStore
from ps2studio.library import favorite_key
from ps2studio.ui import PS2StudioApp


def original_demo_cover(path: Path, title: str, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (420, 600), color)
    draw = ImageDraw.Draw(image)
    for index in range(0, 600, 8):
        tint = tuple(max(0, min(255, value + index // 16 - 40)) for value in color)
        draw.rectangle((0, index, 420, index + 8), fill=tint)
    for index in range(7):
        left = 35 + index * 22
        draw.polygon([(left, 460), (left + 35, 130), (left + 80, 460)], outline="#82d9ff", width=4)
    draw.rectangle((24, 38, 396, 128), fill="#07192f")
    draw.text((42, 58), title.upper(), fill="#ffffff")
    draw.text((42, 522), "CARÁTULA FICTICIA · DEMO", fill="#e5f3ff")
    image.save(path)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ps2studio-capture-") as temp:
        folder = Path(temp)
        games = folder / "Biblioteca de prueba"
        games.mkdir()
        titles = ["Neon Circuit", "Aqua Relic", "Iron Echo", "Shadow Arena"]
        colors = [(24, 45, 100), (15, 96, 132), (67, 64, 132), (120, 63, 33)]
        files = []
        for i, (title, color) in enumerate(zip(titles, colors)):
            filename = games / (title + (".iso" if i % 2 == 0 else ".chd"))
            with filename.open("wb") as output:
                output.truncate((700 + i * 300) * 1024 * 1024)  # sparse demo, never launched
            original_demo_cover(filename.with_suffix(".png"), title, color)
            files.append(filename)
        settings = AppConfig(
            game_directories=[str(games)],
            favorites=[favorite_key(files[0]), favorite_key(files[2])],
        )
        store = ConfigStore(folder / "settings.json")
        store.save(settings)
        root = tk.Tk()
        root.geometry("1170x700+80+60")
        app = PS2StudioApp(root, config_store=store)
        root.update_idletasks()
        root.update()
        first = next(
            (iid for iid, game in app.visible.items() if game.title == "Neon Circuit"), None
        )
        if first is not None:
            app.tree.selection_set(first)
            app.tree.see(first)
        app._show_preview()
        root.update_idletasks()
        root.update()
        time.sleep(0.3)
        top_x, top_y = root.winfo_rootx(), root.winfo_rooty()
        image = ImageGrab.grab(
            bbox=(top_x, top_y, top_x + root.winfo_width(), top_y + root.winfo_height())
        )
        destination = Path("site/assets/app-real-demo.png")
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination)
        root.destroy()
        print(f"Actual Tkinter app screenshot saved to {destination}, size {image.size}")


if __name__ == "__main__":
    main()
