"""Native Windows desktop GUI using standard-library tkinter/ttk."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .config import AppConfig, ConfigError, ConfigStore
from .cover_art import CoverError, validate_cover, suggested_cover
from .play_engine import LaunchError, find_bundled_play, start_play
from .library import Game, favorite_key, filter_games, scan_games


class PS2StudioApp:
    def __init__(self, root: tk.Tk, config_store: ConfigStore | None = None):
        self.root = root
        self.store = config_store or ConfigStore()
        try:
            self.settings = self.store.load()
        except ConfigError as exc:
            messagebox.showwarning("Ajustes dañados", f"{exc}\nSe usarán valores iniciales; el archivo original no ha sido reemplazado.")
            self.settings = AppConfig()
        self.games: list[Game] = []
        self.visible: dict[str, Game] = {}
        self.search_var = tk.StringVar()
        self.favorite_paths = set(self.settings.favorites)
        self.favorites_only_var = tk.BooleanVar(value=False)
        self.fullscreen_var = tk.BooleanVar(value=self.settings.fullscreen)
        self.recursive_var = tk.BooleanVar(value=self.settings.recursive)
        self.status_var = tk.StringVar(value="Listo")
        self.cover_photo = None
        self.details_title = tk.StringVar(value="Selecciona un juego")
        self.details_text = tk.StringVar(value="No hay juego seleccionado.")
        self.engine_path = find_bundled_play()
        self._configure_window()
        self._build_widgets()
        self.refresh_games()

    def _configure_window(self) -> None:
        self.root.title("PS2 Studio — Biblioteca PS2")
        self.root.geometry("1170x700")
        self.root.minsize(950, 560)
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10), background="#ffffff", fieldbackground="#ffffff", foreground="#193052")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"), foreground="#1c5aa6")
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Play.TButton", padding=(18, 9), background="#1768c8", foreground="#ffffff")

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        title = ttk.Frame(outer)
        title.pack(fill="x", pady=(0, 14))
        ttk.Label(title, text="PS2 Studio", style="Title.TLabel").pack(side="left")
        ttk.Label(title, text="Biblioteca local · Motor Play! (experimental)", style="Sub.TLabel").pack(side="left", padx=16, pady=12)

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Añadir carpeta", command=self.add_folder).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Quitar carpeta", command=self.remove_folder).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Actualizar", command=self.refresh_games).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="★ Favorito", command=self.toggle_favorite).pack(side="left")

        paths_frame = ttk.Frame(outer)
        paths_frame.pack(fill="x", pady=(0, 8))
        self.exe_label = ttk.Label(paths_frame, text="", wraplength=860)
        self.exe_label.pack(anchor="w")
        self.paths_label = ttk.Label(paths_frame, text="", wraplength=860)
        self.paths_label.pack(anchor="w")
        self._refresh_path_labels()

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(3, 9))
        ttk.Label(options, text="Buscar:").pack(side="left")
        search = ttk.Entry(options, textvariable=self.search_var)
        search.pack(side="left", fill="x", expand=True, padx=(8, 14))
        self.search_var.trace_add("write", lambda *_: self._render_games())
        ttk.Checkbutton(options, text="Pantalla completa", variable=self.fullscreen_var, command=self._save_options).pack(side="left", padx=(0, 9))
        ttk.Checkbutton(options, text="Subcarpetas", variable=self.recursive_var, command=self._change_recursive).pack(side="left", padx=(0, 9))
        ttk.Checkbutton(options, text="Solo favoritos", variable=self.favorites_only_var, command=self._render_games).pack(side="left")

        horizontal = ttk.Panedwindow(outer, orient="horizontal")
        horizontal.pack(fill="both", expand=True)
        panel = ttk.Frame(horizontal)
        horizontal.add(panel, weight=3)
        details = ttk.Frame(horizontal, padding=(12, 4))
        horizontal.add(details, weight=1)
        columns = ("favorite", "title", "format", "size", "folder")
        self.tree = ttk.Treeview(panel, columns=columns, show="headings", selectmode="browse")
        for key, caption in [("favorite", "★"), ("title", "Juego"), ("format", "Formato"), ("size", "Tamaño"), ("folder", "Carpeta")]:
            self.tree.heading(key, text=caption)
        self.tree.column("favorite", width=42, minwidth=36, stretch=False, anchor="center")
        self.tree.column("title", width=310, minwidth=180, stretch=True)
        self.tree.column("format", width=90, minwidth=70, stretch=False)
        self.tree.column("size", width=100, minwidth=80, stretch=False)
        self.tree.column("folder", width=260, minwidth=150, stretch=True)
        scroll = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _: self.play_selected())
        self.tree.bind("<Return>", lambda _: self.play_selected())
        self.tree.bind("<<TreeviewSelect>>", lambda _: self._show_preview())

        ttk.Label(details, text="CARÁTULA Y DETALLES", font=("Segoe UI", 11, "bold"), foreground="#1c5aa6").pack(anchor="w", pady=(0, 9))
        self.cover_label = tk.Label(details, text="SIN CARÁTULA", bg="#172c4b", fg="#d9e9ff",
                                    font=("Segoe UI", 11, "bold"), width=29, height=13)
        self.cover_label.pack(fill="both", pady=(0, 10))
        ttk.Label(details, textvariable=self.details_title, font=("Segoe UI", 13, "bold"),
                  wraplength=235).pack(anchor="w")
        ttk.Label(details, textvariable=self.details_text, wraplength=235,
                  justify="left").pack(anchor="w", pady=(8, 12))
        image_buttons = ttk.Frame(details)
        image_buttons.pack(anchor="w")
        ttk.Button(image_buttons, text="Elegir carátula", command=self.choose_cover).pack(side="left", padx=(0, 6))
        ttk.Button(image_buttons, text="Quitar", command=self.remove_cover).pack(side="left")
        ttk.Label(details, text="PNG o GIF local · Sin descargas de Internet",
                  foreground="#586b89", wraplength=235).pack(anchor="w", pady=(12, 0))

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Label(footer, textvariable=self.status_var).pack(side="left")
        ttk.Button(footer, text="Web oficial Play!", command=lambda: webbrowser.open("https://purei.org/")).pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Iniciar juego", style="Play.TButton", command=self.play_selected).pack(side="right")

    def _refresh_path_labels(self) -> None:
        self.exe_label.configure(text=f"Emulador: {self.engine_path or '(motor integrado no encontrado)'}")
        self.paths_label.configure(text="Juegos: " + (" | ".join(self.settings.game_directories) or "(añade una carpeta)") )

    def _save_options(self) -> None:
        self.settings.fullscreen = self.fullscreen_var.get()
        self.settings.recursive = self.recursive_var.get()
        try:
            self.store.save(self.settings)
        except ConfigError as exc:
            messagebox.showerror("Error guardando ajustes", str(exc))

    def _change_recursive(self) -> None:
        self._save_options()
        self.refresh_games()

    def add_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Carpeta de juegos PS2")
        if not chosen or chosen in self.settings.game_directories:
            return
        self.settings.game_directories.append(chosen)
        self._save_options()
        self._refresh_path_labels()
        self.refresh_games()

    def remove_folder(self) -> None:
        if not self.settings.game_directories:
            messagebox.showinfo("Carpetas", "No hay carpetas configuradas.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Quitar carpeta")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("560x250")
        ttk.Label(dialog, text="Selecciona la carpeta que quieres quitar:").pack(anchor="w", padx=15, pady=12)
        chooser = ttk.Combobox(dialog, values=self.settings.game_directories, state="readonly")
        chooser.pack(fill="x", padx=15)
        chooser.current(0)

        def confirm() -> None:
            folder = chooser.get()
            self.settings.game_directories.remove(folder)
            self._save_options()
            self._refresh_path_labels()
            self.refresh_games()
            dialog.destroy()

        ttk.Button(dialog, text="Quitar (no borra archivos)", command=confirm).pack(pady=20)

    def _selected_game(self) -> Game | None:
        selected = self.tree.selection()
        return self.visible.get(selected[0]) if selected else None

    def choose_cover(self) -> None:
        game = self._selected_game()
        if game is None:
            messagebox.showinfo("Carátulas", "Selecciona un juego de la lista.")
            return
        path = filedialog.askopenfilename(
            title="Seleccionar carátula local",
            filetypes=[("Carátulas PNG/GIF", "*.png *.gif"), ("PNG", "*.png"), ("GIF", "*.gif")],
        )
        if not path:
            return
        try:
            cover = validate_cover(path)
            # Verify that Tk can decode this file before storing its path.
            probe = tk.PhotoImage(file=str(cover))
            del probe
        except (CoverError, tk.TclError) as exc:
            messagebox.showerror("Carátula no válida", str(exc))
            return
        self.settings.covers[favorite_key(game.path)] = str(cover)
        self._save_options()
        self._show_preview()

    def remove_cover(self) -> None:
        game = self._selected_game()
        if game is None:
            return
        self.settings.covers.pop(favorite_key(game.path), None)
        self._save_options()
        self._show_preview()

    def _show_preview(self) -> None:
        game = self._selected_game()
        self.cover_photo = None
        if game is None:
            self.details_title.set("Selecciona un juego")
            self.details_text.set("Las carátulas se guardan como rutas locales.")
            self.cover_label.configure(image="", text="SIN CARÁTULA", width=29, height=13)
            return
        self.details_title.set(game.title)
        self.details_text.set(
            f"Formato: {game.format}\nTamaño: {game.size_label}\nCarpeta: {game.path.parent}"
        )
        requested = self.settings.covers.get(favorite_key(game.path))
        try:
            cover = validate_cover(requested) if requested else suggested_cover(game.path)
            if cover is not None:
                photo = tk.PhotoImage(file=str(cover))
                scale = max(1, (photo.width() + 239) // 240, (photo.height() + 279) // 280)
                if scale > 1:
                    photo = photo.subsample(scale, scale)
                self.cover_photo = photo
                self.cover_label.configure(image=photo, text="", width=240, height=280)
                return
        except (CoverError, tk.TclError, OSError):
            pass
        self.cover_label.configure(image="", text="SIN CARÁTULA", width=29, height=13)

    def toggle_favorite(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Favoritos", "Selecciona un juego de la lista.")
            return
        game = self.visible.get(selection[0])
        if game is None:
            return
        key = favorite_key(game.path)
        if key in self.favorite_paths:
            self.favorite_paths.remove(key)
        else:
            self.favorite_paths.add(key)
        self.settings.favorites = sorted(self.favorite_paths)
        self._save_options()
        self._render_games()

    def refresh_games(self) -> None:
        self.games = scan_games(self.settings.game_directories, recursive=self.recursive_var.get())
        self._render_games()

    def _render_games(self) -> None:
        filtered = filter_games(
            self.games, self.search_var.get(),
            favorite_paths=self.favorite_paths,
            favorites_only=self.favorites_only_var.get(),
        )
        previous = self._selected_game()
        previous_path = previous.path if previous else None
        self.visible.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, game in enumerate(filtered):
            item_id = str(index)
            self.visible[item_id] = game
            symbol = "★" if favorite_key(game.path) in self.favorite_paths else ""
            self.tree.insert("", "end", iid=item_id, values=(symbol, game.title, game.format, game.size_label, str(game.path.parent)))
            if previous_path == game.path:
                self.tree.selection_set(item_id)
        self.status_var.set(f"{len(filtered)} juegos visibles · {len(self.games)} encontrados · {len(self.favorite_paths)} favoritos")
        self._show_preview()

    def play_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Selecciona un juego", "Elige un juego de la lista.")
            return
        game = self.visible.get(selection[0])
        if game is None:
            return
        try:
            if self.engine_path is None:
                raise LaunchError("Falta el motor Play! integrado en esta distribución experimental.")
            start_play(self.engine_path, game.path, fullscreen=self.fullscreen_var.get())
        except LaunchError as exc:
            messagebox.showerror("No se pudo iniciar", str(exc))
            return
        self.status_var.set(f"Iniciado: {game.title}")


def main() -> None:
    root = tk.Tk()
    PS2StudioApp(root)
    root.mainloop()
