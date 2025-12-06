import shutil
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog
import os
import sys

from tkinterdnd2 import TkinterDnD, DND_FILES


# ---------------------------------------------------------
#  Global settings
# ---------------------------------------------------------
ctk.set_appearance_mode("system")        # system / light / dark
ctk.set_default_color_theme("blue")      # blue / green / dark-blue


# ---------------------------------------------------------
#  Application class with Drag & Drop support
# ---------------------------------------------------------
class MoveByExtApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        # ------------------- Window icon --------------------
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "sort.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass

        # ------------------- Main window --------------------
        self.title("Sort – find and move files by extension")
        self.geometry("700x450")
        self.minsize(650, 400)

        # Main CTk container inside TkinterDnD.Tk
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        self.root_dir = Path.cwd()
        self.recurse_var = ctk.BooleanVar(value=True)

        # ---------------------------------------------------------
        #  Top frame: folder selection
        # ---------------------------------------------------------
        top_frame = ctk.CTkFrame(container)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.dir_label = ctk.CTkLabel(
            top_frame,
            text=f"Start folder: {self.root_dir}",
            anchor="w"
        )
        self.dir_label.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)

        choose_btn = ctk.CTkButton(
            top_frame,
            text="Choose folder",
            command=self.choose_folder
        )
        choose_btn.pack(side="right", padx=(5, 10), pady=10)

        # ---------------------------------------------------------
        #  Middle frame: parameters
        # ---------------------------------------------------------
        middle_frame = ctk.CTkFrame(container)
        middle_frame.pack(fill="x", padx=10, pady=5)

        ext_label = ctk.CTkLabel(middle_frame, text="Extension (without dot):")
        ext_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(10, 5))

        self.ext_entry = ctk.CTkEntry(middle_frame, width=120, placeholder_text="e.g. mp4")
        self.ext_entry.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(10, 5))

        recurse_cb = ctk.CTkCheckBox(
            middle_frame,
            text="Search in subfolders",
            variable=self.recurse_var
        )
        recurse_cb.grid(row=0, column=2, sticky="w", padx=(10, 10), pady=(10, 5))

        start_btn = ctk.CTkButton(
            middle_frame,
            text="Start moving",
            command=self.start_move
        )
        start_btn.grid(row=0, column=3, sticky="e", padx=(10, 10), pady=(10, 5))

        middle_frame.grid_columnconfigure(2, weight=1)

        # ---------------------------------------------------------
        #  Log area
        # ---------------------------------------------------------
        log_frame = ctk.CTkFrame(container)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        log_label = ctk.CTkLabel(
            log_frame,
            text="Operation log (you can also DRAG & DROP a folder onto this window):"
        )
        log_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log("Ready. Choose a folder, enter an extension and click Start.")
        self.log("You can also drag & drop a folder from Explorer onto this window.\n")

        # ---------------------------------------------------------
        #  Drag & drop registration for the whole window
        # ---------------------------------------------------------
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop)

    # ---------------------------------------------------------
    #  Helper methods
    # ---------------------------------------------------------
    def log(self, msg: str):
        """Append a line to the log textbox."""
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def choose_folder(self):
        """Show a folder selection dialog and set the start folder."""
        selected = filedialog.askdirectory(initialdir=str(self.root_dir))
        if selected:
            self.set_root_dir(Path(selected))

    def set_root_dir(self, path: Path):
        """Set the start folder, update label and log."""
        self.root_dir = path
        self.dir_label.configure(text=f"Start folder: {self.root_dir}")
        self.log(f"Start folder set to: {self.root_dir}")

    # ---------------------------------------------------------
    #  Drag & drop handler
    # ---------------------------------------------------------
    def on_drop(self, event):
        raw = event.data
        paths = self._parse_dropped_paths(raw)
        if not paths:
            return

        p = paths[0]

        # If a file was dropped, use its parent folder
        if p.is_file():
            p = p.parent

        if p.is_dir():
            self.set_root_dir(p)
        else:
            self.log(f"⚠ Dropped item is not a folder: {p}")

    def _parse_dropped_paths(self, data: str):
        """
        Convert DND_FILES string into a list of Path objects.
        Handles { } wrapping from Explorer and multiple paths.
        """
        paths = []
        # splitlist correctly splits the DND_FILES string
        for part in self.tk.splitlist(data):
            part = part.strip().strip("{}")  # remove spaces and surrounding {}
            if part:
                paths.append(Path(part))
        return paths

    # ---------------------------------------------------------
    #  Start moving
    # ---------------------------------------------------------
    def start_move(self):
        ext = self.ext_entry.get().strip().lower().lstrip(".")
        if not ext:
            self.log("❌ No extension provided!")
            return

        if not self.root_dir.exists():
            self.log(f"❌ Folder does not exist: {self.root_dir}")
            return

        self.log_text.delete("1.0", "end")
        self.log(f"Starting to move *.{ext} from folder: {self.root_dir}")
        self.log(f"Search subfolders: {'YES' if self.recurse_var.get() else 'NO'}")

        self.move_files_by_extension(ext)

    # ---------------------------------------------------------
    #  Core moving logic
    # ---------------------------------------------------------
    def move_files_by_extension(self, ext: str):
        root = self.root_dir
        recurse = self.recurse_var.get()

        dst = root / ext
        dst.mkdir(exist_ok=True)
        self.log(f"Destination folder: {dst}")

        if recurse:
            candidates = root.rglob(f"*.{ext}")
        else:
            candidates = root.glob(f"*.{ext}")

        moved = 0

        for src in candidates:
            if src.is_dir():
                continue

            # Skip files already in destination folder
            if src.parent == dst:
                continue

            try:
                target = dst / src.name
                shutil.move(str(src), str(target))
                self.log(f"Moved: {src} -> {target}")
                moved += 1
            except Exception as e:
                self.log(f"⚠ Error: {src} -> {e}")

        self.log("")
        self.log(f"Done. Moved: {moved} file(s).")


# ---------------------------------------------------------
#  Application entry point
# ---------------------------------------------------------
if __name__ == "__main__":
    app = MoveByExtApp()
    app.mainloop()
