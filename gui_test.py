import tkinter as tk
from tkinter import colorchooser, simpledialog

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Overlay")
        self.root.geometry("400x100+100+100")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.7)
        self.text_label = tk.Label(self.root, text="Your text will appear here", bg="white", font=("Helvetica", 16))
        self.text_label.pack(expand=True, fill="both")

        # Settings icon
        self.settings_icon = tk.Label(self.root, text="⚙", font=("Helvetica", 14), fg="black")
        self.settings_icon.pack(anchor="ne")
        self.settings_icon.bind("<Button-1>", self.open_settings)

        # Initialize variables for dragging and resizing
        self.start_x = 0
        self.start_y = 0
        self.drag_enabled = False

        # Bind the events for dragging the window
        self.root.bind("<ButtonPress-1>", self.on_drag_start)
        self.root.bind("<B1-Motion>", self.on_drag_motion)

        # Menu for settings
        self.settings_menu = tk.Menu(self.root, tearoff=0)
        self.settings_menu.add_command(label="Toggle Dragging", command=self.toggle_dragging)
        self.settings_menu.add_command(label="Toggle Resizing", command=self.toggle_resizing)
        self.settings_menu.add_command(label="Change Background Color", command=self.change_color)
        self.settings_menu.add_command(label="Change Translucency", command=self.change_translucency)

    def open_settings(self, event):
        self.settings_menu.tk_popup(event.x_root, event.y_root)

    def toggle_dragging(self):
        self.drag_enabled = not self.drag_enabled

    def toggle_resizing(self):
        if self.root.overrideredirect():
            self.root.overrideredirect(False)
        else:
            self.root.overrideredirect(True)

    def change_color(self):
        color = colorchooser.askcolor(title="Choose background color")[1]
        if color:
            self.root.config(bg=color)
            self.text_label.config(bg=color)

    def change_translucency(self):
        alpha = simpledialog.askfloat("Translucency", "Enter value (0.1 - 1.0):", minvalue=0.1, maxvalue=1.0)
        if alpha is not None:
            self.root.attributes('-alpha', alpha)

    def on_drag_start(self, event):
        if self.drag_enabled:
            self.start_x = event.x
            self.start_y = event.y

    def on_drag_motion(self, event):
        if self.drag_enabled:
            x = self.root.winfo_x() + (event.x - self.start_x)
            y = self.root.winfo_y() + (event.y - self.start_y)
            self.root.geometry(f"+{x}+{y}")

    def update_text(self, new_text):
        self.text_label.config(text=new_text)
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = GUI()
    gui.run()
