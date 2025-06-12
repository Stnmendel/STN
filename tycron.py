import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageDraw

class Tycron(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tycron")
        self.geometry("800x600")
        self.canvas = tk.Canvas(self, bg='white', width=800, height=550)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bind_events()
        self.setup_menu()
        self.image = Image.new('RGB', (800, 550), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None
        self.color = 'black'
        self.brush_size = 3

    def bind_events(self):
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.reset)

    def setup_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='New', command=self.new_page)
        filemenu.add_command(label='Open', command=self.open_image)
        filemenu.add_command(label='Save', command=self.save_image)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label='Brush Color', command=self.choose_color)
        menubar.add_cascade(label='Tools', menu=toolsmenu)

        self.config(menu=menubar)

    def new_page(self):
        self.canvas.delete('all')
        self.image = Image.new('RGB', (800, 550), 'white')
        self.draw = ImageDraw.Draw(self.image)

    def open_image(self):
        filepath = filedialog.askopenfilename(filetypes=[('PNG Images', '*.png')])
        if not filepath:
            return
        img = tk.PhotoImage(file=filepath)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor='nw', image=img)
        self.canvas.image = img
        self.image = Image.open(filepath)
        self.draw = ImageDraw.Draw(self.image)

    def save_image(self):
        filepath = filedialog.asksaveasfilename(defaultextension='.png',
                                                filetypes=[('PNG Images', '*.png')])
        if filepath:
            self.image.save(filepath)

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.color)
        if color[1]:
            self.color = color[1]

    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y

    def on_drag(self, event):
        if self.last_x is not None and self.last_y is not None:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    fill=self.color, width=self.brush_size,
                                    capstyle=tk.ROUND, smooth=True)
            self.draw.line((self.last_x, self.last_y, event.x, event.y),
                           fill=self.color, width=self.brush_size)
        self.last_x, self.last_y = event.x, event.y

    def reset(self, event):
        self.last_x, self.last_y = None, None

if __name__ == '__main__':
    app = Tycron()
    app.mainloop()
