import tkinter as tk
from tkinter import colorchooser, simpledialog, font
from tkinter.ttk import Combobox
import queue

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Overlay")
        self.root.geometry("400x100+100+100")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.7)
        self.overrideredirect_enabled = True

        self.default_font = ("Helvetica", 18)
        self.default_font_color = "black"
        self.text_label = tk.Label(self.root, text="Your text will appear here",
                                   fg=self.default_font_color, bg="white")
        self.text_label.pack(expand=True, fill="both")
        self.text_label.configure(font=self.default_font)

        # Settings icon
        self.settings_icon = tk.Label(self.root, text="⚙",
                                      font=self.default_font,
                                      fg=self.default_font_color,
                                      cursor="hand2")
        self.settings_icon.pack(anchor="ne")
        self.settings_icon.bind("<Button-1>", self.open_settings)

        # Initialize variables for dragging
        self.start_x = 0
        self.start_y = 0
        self.drag_enabled = False

        # Bind events for dragging
        self.root.bind("<ButtonPress-1>", self.on_drag_start)
        self.root.bind("<B1-Motion>", self.on_drag_motion)

        # Menu for settings
        self.settings_menu = tk.Menu(self.root, tearoff=0)
        self.settings_menu.add_command(label="Toggle Dragging", command=self.toggle_dragging)
        self.settings_menu.add_command(label="Toggle Resizing", command=self.toggle_resizing)
        self.settings_menu.add_command(label="Change Background Color", command=self.change_color)
        self.settings_menu.add_command(label="Change Translucency", command=self.change_translucency)
        self.settings_menu.add_command(label="Change Font", command=self.change_font)
        self.settings_menu.add_command(label="Change Font Size", command=self.change_font_size)
        self.settings_menu.add_command(label="Change Font Color", command=self.change_font_color)
        self.settings_menu.add_command(label="Exit", command=self.exit_app)

        # Queue for thread communication
        self.queue = queue.Queue()

        # Update GUI periodically from the queue
        self.update_gui()

    def open_settings(self, event):
        self.settings_menu.tk_popup(event.x_root, event.y_root)

    def toggle_dragging(self):
        self.drag_enabled = not self.drag_enabled

    def toggle_resizing(self):
        self.overrideredirect_enabled = not self.overrideredirect_enabled
        self.root.overrideredirect(self.overrideredirect_enabled)

    def change_color(self):
        color = colorchooser.askcolor(title="Choose background color")[1]
        if color:
            self.root.config(bg=color)
            self.text_label.config(bg=color)

    def change_translucency(self):
        alpha = simpledialog.askfloat("Translucency", "Enter value (0.1 - 1.0):", minvalue=0.1, maxvalue=1.0)
        if alpha is not None:
            self.root.attributes('-alpha', alpha)

    def change_font(self):
        font_window = tk.Toplevel(self.root)
        font_window.title("Select Font")
        font_window.geometry("200x150")
        font_window.transient(self.root)  # Make the window modal

        font_combobox = Combobox(font_window, values=sorted(font.families()), width=20)
        font_combobox.pack(pady=10)

        def font_selected(event):
            selected_font = font_combobox.get()
            if selected_font:
                self.default_font = (selected_font, self.default_font[1])
                self.text_label.configure(font=self.default_font, fg=self.default_font_color)
                self.settings_icon.configure(font=self.default_font, fg=self.default_font_color)
                font_window.destroy()

        font_combobox.bind("<<ComboboxSelected>>", font_selected)

    def change_font_size(self):
        font_size = simpledialog.askinteger("Font Size", "Enter font size:", initialvalue=self.default_font[1])

        if font_size:
            self.default_font = (self.default_font[0], font_size)
            self.text_label.configure(font=self.default_font, fg=self.default_font_color)
            self.settings_icon.configure(font=self.default_font, fg=self.default_font_color)
            
    def change_font_color(self):
        color = colorchooser.askcolor(title="Choose font color")[1]
        if color:
            self.default_font_color = color
            self.text_label.configure(font=self.default_font, fg=self.default_font_color)
            self.settings_icon.configure(font=self.default_font, fg=self.default_font_color)

    def on_drag_start(self, event):
        if self.drag_enabled:
            self.start_x = event.x
            self.start_y = event.y

    def on_drag_motion(self, event):
        if self.drag_enabled:
            x = self.root.winfo_x() + (event.x - self.start_x)
            y = self.root.winfo_y() + (event.y - self.start_y)
            self.root.geometry(f"+{x}+{y}")

    def exit_app(self):
        self.root.destroy()

    def update_text(self, text):
        self.text_label.config(text=text)

    def update_gui(self):
        while not self.queue.empty():
            text = self.queue.get_nowait()
            self.update_text(text)
        self.root.after(100, self.update_gui)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = GUI()
    gui.run()
