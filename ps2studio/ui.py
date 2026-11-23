"""Native Windows desktop GUI using standard-library tkinter/ttk."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .autodetect import find_pcsx2
from .config import AppConfig, ConfigError, ConfigStore
from .launcher import LaunchError, start_game
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
        self._auto_detect_pcsx2()
        self._configure_window()
        self._build_widgets()
        self.refresh_games()

    def _configure_window(self) -> None:
        self.root.title("PS2 Studio — Biblioteca PS2")
        self.root.geometry("980x650")
        self.root.minsize(740, 480)
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=31, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Play.TButton", padding=(18, 9))

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        title = ttk.Frame(outer)
        title.pack(fill="x", pady=(0, 14))
        ttk.Label(title, text="PS2 Studio", style="Title.TLabel").pack(side="left")
        ttk.Label(title, text="Biblioteca local · Motor PCSX2", style="Sub.TLabel").pack(side="left", padx=16, pady=12)

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Seleccionar PCSX2", command=self.choose_emulator).pack(side="left", padx=(0, 6))
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

        panel = ttk.Frame(outer)
        panel.pack(fill="both", expand=True)
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

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Label(footer, textvariable=self.status_var).pack(side="left")
        ttk.Button(footer, text="Web oficial PCSX2", command=lambda: webbrowser.open("https://pcsx2.net/downloads/")).pack(side="right", padx=(8, 0))
        ttk.Button(footer, text="Iniciar juego", style="Play.TButton", command=self.play_selected).pack(side="right")

    def _auto_detect_pcsx2(self) -> None:
        current = self.settings.pcsx2_path
        if current and Path(current).is_file() and Path(current).name.lower() in {"pcsx2-qt.exe", "pcsx2.exe"}:
            return
        detected = find_pcsx2()
        if detected:
            self.settings.pcsx2_path = detected
            try:
                self.store.save(self.settings)
            except ConfigError as exc:
                messagebox.showwarning("Detección de PCSX2", f"Se detectó PCSX2 pero no se pudieron guardar los ajustes: {exc}")
            self.status_var.set("PCSX2 detectado automáticamente")

    def _refresh_path_labels(self) -> None:
        # The best-effort detector runs only at startup; manual selection remains possible.
        self.exe_label.configure(text=f"Emulador: {self.settings.pcsx2_path or '(sin configurar)'}")
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

    def choose_emulator(self) -> None:
        chosen = filedialog.askopenfilename(title="Seleccionar PCSX2", filetypes=[("PCSX2", "pcsx2-qt.exe pcsx2.exe"), ("Ejecutables", "*.exe")])
        if not chosen:
            return
        if Path(chosen).name.lower() not in {"pcsx2-qt.exe", "pcsx2.exe"}:
            messagebox.showerror("Archivo no válido", "Selecciona pcsx2-qt.exe o pcsx2.exe")
            return
        self.settings.pcsx2_path = chosen
        self._save_options()
        self._refresh_path_labels()

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
        self.visible.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, game in enumerate(filtered):
            item_id = str(index)
            self.visible[item_id] = game
            symbol = "★" if favorite_key(game.path) in self.favorite_paths else ""
            self.tree.insert("", "end", iid=item_id, values=(symbol, game.title, game.format, game.size_label, str(game.path.parent)))
        self.status_var.set(f"{len(filtered)} juegos visibles · {len(self.games)} encontrados · {len(self.favorite_paths)} favoritos")

    def play_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Selecciona un juego", "Elige un juego de la lista.")
            return
        game = self.visible.get(selection[0])
        if game is None:
            return
        try:
            start_game(self.settings.pcsx2_path, game.path, fullscreen=self.fullscreen_var.get())
        except LaunchError as exc:
            messagebox.showerror("No se pudo iniciar", str(exc))
            return
        self.status_var.set(f"Iniciado: {game.title}")


def main() -> None:
    root = tk.Tk()
    PS2StudioApp(root)
    root.mainloop()
