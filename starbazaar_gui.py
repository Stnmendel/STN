import os
import json
import io
import time
import threading
import requests
from tkinter import Tk, messagebox, ttk, StringVar, Frame, Label, Button, Entry, OptionMenu, LabelFrame, Toplevel, Listbox
from tkinter import colorchooser
from PIL import Image, ImageTk
from cryptography.fernet import Fernet

# ==============================================================================
# Load brand list
# ==============================================================================
BRAND_FILE = os.path.join('data', 'brands.json')
if not os.path.exists(BRAND_FILE):
    raise FileNotFoundError('brands.json not found')
with open(BRAND_FILE, 'r', encoding='utf-8') as f:
    BRAND_IDS = json.load(f)
REVERSED_BRAND_IDS = {v: k for k, v in BRAND_IDS.items() if v is not None}

# ==============================================================================
# Settings management
# ==============================================================================
SETTINGS_FILE = 'settings.json'
default_settings = {
    "APP_BG_COLOR": "#FFD1DC",
    "FRAME_BG_COLOR": "#FFC0CB",
    "BUTTON_BG_COLOR": "#FF69B4",
    "BUTTON_FG_COLOR": "white",
    "ITEM_BG_COLOR": "#FFE4E1",
    "LABEL_TEXT_COLOR": "#8B0000"
}

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
else:
    settings = default_settings.copy()

def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

APP_BG_COLOR = settings["APP_BG_COLOR"]
FRAME_BG_COLOR = settings["FRAME_BG_COLOR"]
BUTTON_BG_COLOR = settings["BUTTON_BG_COLOR"]
BUTTON_FG_COLOR = settings["BUTTON_FG_COLOR"]
ITEM_BG_COLOR = settings["ITEM_BG_COLOR"]
LABEL_TEXT_COLOR = settings["LABEL_TEXT_COLOR"]

# ==============================================================================
# Cookie encryption helpers
# ==============================================================================
COOKIE_FILE = 'cookies.dat'
KEY_FILE = 'key.key'

def write_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def load_key():
    return open(KEY_FILE, 'rb').read()

def save_encrypted_cookies(cookies):
    if not os.path.exists(KEY_FILE):
        key = write_key()
    else:
        key = load_key()
    f = Fernet(key)
    enc = f.encrypt(json.dumps(cookies).encode('utf-8'))
    with open(COOKIE_FILE, 'wb') as fp:
        fp.write(enc)

def load_decrypted_cookies():
    if not os.path.exists(COOKIE_FILE) or not os.path.exists(KEY_FILE):
        return None
    key = load_key()
    f = Fernet(key)
    with open(COOKIE_FILE, 'rb') as fp:
        data = fp.read()
    try:
        dec = f.decrypt(data)
        return json.loads(dec.decode('utf-8'))
    except Exception:
        return None

# ==============================================================================
# Global state
# ==============================================================================
YOUR_STARDOLL_COOKIES = {}
watchlist = []
wishlist = []

is_searching = False
pause_event = threading.Event()

# ==============================================================================
# Tkinter helper classes
# ==============================================================================
class AutocompleteEntry(ttk.Entry):
    def __init__(self, parent, completions, *args, **kwargs):
        self.var = kwargs.get('textvariable', StringVar())
        kwargs['textvariable'] = self.var
        super().__init__(parent, *args, **kwargs)
        self.completions = completions
        self.listbox_up = False
        self.var.trace('w', self.changed)
        self.bind('<Down>', self.move_down)
        self.bind('<Up>', self.move_up)
        self.bind('<Return>', self.selection)
        self.bind('<Right>', self.selection)

    def changed(self, *args):
        if self.var.get() == '':
            self.hide_listbox()
        else:
            words = self.comparison()
            if words:
                if not self.listbox_up:
                    x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
                    y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.winfo_height()
                    self.listbox = Listbox(self.winfo_toplevel(), width=self.winfo_width(), height=6)
                    self.listbox.bind('<Double-Button-1>', self.selection)
                    self.listbox.bind('<Return>', self.selection)
                    self.listbox.place(x=x, y=y)
                    self.listbox_up = True
                self.listbox.delete(0, 'end')
                for w in words:
                    self.listbox.insert('end', w)
            else:
                self.hide_listbox()

    def selection(self, event=None):
        if self.listbox_up and self.listbox.curselection():
            self.var.set(self.listbox.get('active'))
            self.hide_listbox()
            self.icursor('end')
            return 'break'

    def hide_listbox(self, event=None):
        if self.listbox_up:
            self.listbox.destroy()
            self.listbox_up = False

    def move_up(self, event):
        if self.listbox_up:
            index = self.listbox.curselection()
            index = 0 if not index else int(index[0])
            if index > 0:
                self.listbox.selection_clear(index)
                self.listbox.selection_set(index-1)
            return 'break'

    def move_down(self, event):
        if self.listbox_up:
            index = self.listbox.curselection()
            index = -1 if not index else int(index[0])
            if index < self.listbox.size()-1:
                self.listbox.selection_clear(index)
                self.listbox.selection_set(index+1)
            return 'break'

    def comparison(self):
        pattern = self.var.get().lower()
        return [w for w in self.completions if w.lower().startswith(pattern)]

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = ttk.Canvas(self, bg=APP_BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0), window=self.scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

# ==============================================================================
# HTTP helpers
# ==============================================================================
def check_cookies(cookies):
    if not cookies:
        return False
    try:
        r = requests.get('https://www.stardoll.com/en/account/', cookies=cookies, allow_redirects=False, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def get_items(item_type, currency_type, min_price, max_price, brand_id=None):
    if not YOUR_STARDOLL_COOKIES:
        return []
    base_url = 'https://www.stardoll.com/en/com/user/getStarBazaar.php'
    params = {'search':'', 'type':item_type, 'currencyType':currency_type,
              'minPrice':min_price, 'maxPrice':max_price}
    if brand_id and item_type != 'hair':
        params['brands'] = brand_id
    try:
        s = requests.Session()
        s.cookies.update(YOUR_STARDOLL_COOKIES)
        resp = s.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('items', [])
    except Exception:
        return []

# ==============================================================================
# Utility functions
# ==============================================================================
def load_image(url, size=(100,100)):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def copy_to_clipboard(text):
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo('Kopyalandı', f"'{text}' panoya kopyalandı")

# ==============================================================================
# Search logic
# ==============================================================================
def perform_search(item_type, currency_type, min_price_input, max_price_input, brand_id, search_keyword):
    global is_searching
    progress['value'] = 0
    total_segments = 30
    step_size = max(1, (max_price_input - min_price_input + 1) // total_segments)
    segments = []
    current = min_price_input
    while current <= max_price_input:
        segments.append((current, min(current+step_size-1, max_price_input)))
        current += step_size
    progress['maximum'] = len(segments)
    all_items = []
    while segments and is_searching:
        pause_event.wait()
        if not is_searching:
            break
        seg = segments.pop(0)
        items = get_items(item_type, currency_type, seg[0], seg[1], brand_id)
        for item in items:
            item_key = 'customItemId' if item_type=='hair' else 'itemId'
            identifier = item.get(item_key)
            price = item.get('sellPrice')
            if any(d.get(item_key)==identifier and d.get('sellPrice')==price for d in all_items):
                continue
            brand_name = 'Bilinmiyor'
            if brand_id is not None:
                brand_name = brand_name_var.get()
            else:
                bid = item.get('brandId')
                if bid:
                    brand_name = REVERSED_BRAND_IDS.get(int(bid), 'Bilinmiyor')
            item['brandName'] = brand_name
            all_items.append(item)
        progress['value'] += 1
        root.update_idletasks()
        time.sleep(0.5)
    if is_searching:
        display_items(filter_items_by_name(all_items, search_keyword), currency_type, item_type, search_keyword)
    is_searching = False
    toggle_search_buttons(False)
    status_label.config(text='Arama tamamlandı', fg='green')


def filter_items_by_name(items, keyword):
    if not keyword:
        return items
    return [i for i in items if keyword.lower() in i.get('name','').lower()]

# ==============================================================================
# Display results
# ==============================================================================
def display_items(items_to_display, currency_type, item_type, search_keyword=''):
    for w in results_frame.scrollable_frame.winfo_children():
        w.destroy()
    if not items_to_display:
        msg = 'Belirtilen filtrelere uygun öğe bulunamadı.'
        Label(results_frame.scrollable_frame, text=msg, bg=APP_BG_COLOR).pack(pady=20)
        return
    columns = 4
    for idx, item in enumerate(items_to_display):
        row = idx // columns
        col = idx % columns
        lf = LabelFrame(results_frame.scrollable_frame, bg=ITEM_BG_COLOR, padx=5, pady=5)
        lf.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        full_url = None
        if item_type=='hair':
            cid = item.get('customItemId')
            if cid:
                full_url = f"http://www.sdcdn.com/customitems/130/{str(cid).zfill(3)[:3]}/435/{cid}.png"
        else:
            iid = item.get('itemId')
            if iid:
                full_url = f"http://cdn.stardoll.com/itemimages/130/0/66/{iid}.png"
        img_label = Label(lf, bg=ITEM_BG_COLOR)
        if full_url:
            photo = load_image(full_url, size=(120,120))
            if photo:
                img_label.config(image=photo)
                img_label.image = photo
            else:
                img_label.config(text='Görsel yok')
        else:
            img_label.config(text='Görsel yok')
        img_label.pack()
        Label(lf, text=item.get('name','?'), bg=ITEM_BG_COLOR).pack()
        Label(lf, text=f"Marka: {item.get('brandName','?')}", bg=ITEM_BG_COLOR).pack()
        cur = 'Stardollars' if currency_type==1 else 'Starcoins'
        Label(lf, text=f"Fiyat: {item.get('sellPrice','?')} {cur}", bg=ITEM_BG_COLOR).pack()
        sid = item.get('sellerId','?')
        seller_frame = Frame(lf, bg=ITEM_BG_COLOR)
        seller_frame.pack(pady=2)
        Label(seller_frame, text=f"Satıcı ID: {sid}", bg=ITEM_BG_COLOR).pack(side='left')
        Button(seller_frame, text='Kopyala', command=lambda s=sid: copy_to_clipboard(str(s)), bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR).pack(side='left', padx=2)
        Button(lf, text='Takip', command=lambda it=item, t=item_type: add_to_watchlist(it, t), bg='#FFA500').pack(pady=2)
        check_wishlist_match(item, item_type)
        check_watchlist_price(item, item_type)

# ==============================================================================
# Watchlist and Wishlist logic
# ==============================================================================
def add_to_watchlist(item, item_type):
    key = 'customItemId' if item_type=='hair' else 'itemId'
    identifier = item.get(key)
    if identifier is None:
        return
    watchlist.append({
        'id': identifier,
        'price': item.get('sellPrice',0),
        'itemType': item_type,
        'name': item.get('name',''),
        'sellerId': item.get('sellerId','')
    })
    update_watchlist_box()


def check_watchlist_price(item, item_type):
    key = 'customItemId' if item_type=='hair' else 'itemId'
    identifier = item.get(key)
    for w in watchlist:
        if w['id']==identifier and item.get('sellPrice',0) < w['price']:
            popup = Toplevel(root)
            popup.title('Fiyat Düşüşü')
            Label(popup, text=f"{w['name']} {w['price']} -> {item['sellPrice']}").pack(pady=5)
            sid = item.get('sellerId','?')
            lbl = Label(popup, text=f"Satıcı ID: {sid}")
            lbl.pack()
            Button(popup, text='Kopyala', command=lambda s=sid: copy_to_clipboard(str(s))).pack(pady=5)
            Button(popup, text='Kapat', command=popup.destroy).pack()
            w['price'] = item['sellPrice']
            break

def update_watchlist_box():
    watchlist_box.delete(0,'end')
    for w in watchlist:
        watchlist_box.insert('end', f"{w['name']} - {w['price']}")


def add_to_wishlist(name):
    name = name.strip()
    if name and name not in wishlist:
        wishlist.append(name)
        wishlist_box.insert('end', name)

def remove_selected_wishlist():
    sel = wishlist_box.curselection()
    if not sel:
        return
    idx = sel[0]
    wishlist.pop(idx)
    wishlist_box.delete(idx)

def check_wishlist_match(item, item_type):
    if item.get('name','') in wishlist:
        popup = Toplevel(root)
        popup.title('Wishlist Eşleşmesi')
        Label(popup, text=f"Wishlist'inizdeki '{item['name']}' bulundu!").pack(pady=5)
        sid = item.get('sellerId','?')
        lbl = Label(popup, text=f"Satıcı ID: {sid}")
        lbl.pack()
        Button(popup, text='Kopyala', command=lambda s=sid: copy_to_clipboard(str(s))).pack(pady=5)
        Button(popup, text='Kapat', command=popup.destroy).pack()

# ==============================================================================
# UI callbacks
# ==============================================================================
def start_search_thread():
    global is_searching
    if is_searching:
        messagebox.showwarning('Uyarı','Zaten bir arama var')
        return
    if not any(YOUR_STARDOLL_COOKIES.values()):
        messagebox.showerror('Hata','Önce çerez bilgilerini girin')
        return
    try:
        min_price = int(min_price_entry.get())
        max_price = int(max_price_entry.get())
        if not (2 <= min_price <= max_price <= 600):
            raise ValueError
    except ValueError:
        messagebox.showerror('Hata','Geçerli fiyat aralığı girin (2-600)')
        return
    is_searching = True
    pause_event.set()
    toggle_search_buttons(True)
    for w in results_frame.scrollable_frame.winfo_children():
        w.destroy()
    item_type = item_type_var.get().lower()
    currency_type = 1 if 'Stardollars' in currency_type_var.get() else 2
    brand_id = BRAND_IDS.get(brand_name_var.get())
    keyword = keyword_entry.get().strip()
    threading.Thread(target=perform_search, args=(item_type,currency_type,min_price,max_price,brand_id,keyword), daemon=True).start()
    status_label.config(text='Arama başladı', fg='blue')


def toggle_search_buttons(running):
    search_button.config(state='disabled' if running else 'normal')
    pause_resume_button.config(state='normal' if running else 'disabled')


def pause_resume_search():
    if pause_event.is_set():
        pause_event.clear()
        pause_resume_button.config(text='Devam Et')
        status_label.config(text='Duraklatıldı', fg='orange')
    else:
        pause_event.set()
        pause_resume_button.config(text='Duraklat')
        status_label.config(text='Devam ediyor', fg='blue')


def reset_application():
    global is_searching
    if is_searching:
        is_searching = False
        pause_event.set()
    for w in results_frame.scrollable_frame.winfo_children():
        w.destroy()
    item_type_var.set(item_type_options[0])
    currency_type_var.set(currency_type_options[0])
    min_price_entry.delete(0,'end'); min_price_entry.insert(0,'2')
    max_price_entry.delete(0,'end'); max_price_entry.insert(0,'600')
    brand_name_var.set(display_brand_options[0])
    keyword_entry.delete(0,'end')
    status_label.config(text='Sıfırlandı', fg='green')
    toggle_search_buttons(False)


def refresh_cookies():
    main_notebook.pack_forget()
    cookie_input_frame.pack(fill='both', expand=True, padx=20, pady=20)


def clear_saved_cookies():
    global YOUR_STARDOLL_COOKIES
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
    YOUR_STARDOLL_COOKIES = {}
    messagebox.showinfo('Bilgi','Kayıtlı çerezler silindi')


def choose_color(setting_key, widget):
    color = colorchooser.askcolor()[1]
    if color:
        settings[setting_key] = color
        widget.config(bg=color)
        save_settings()

# ==============================================================================
# Build UI
# ==============================================================================
root = Tk()
root.title('Stardoll Starbazaar Filtreleyici')
root.geometry('1024x768')
root.configure(bg=APP_BG_COLOR)

style = ttk.Style()
style.configure('TFrame', background=APP_BG_COLOR)

main_notebook = ttk.Notebook(root)

# Frames
main_app_frame = Frame(main_notebook, bg=APP_BG_COLOR)
watch_frame = Frame(main_notebook, bg=APP_BG_COLOR)
wishlist_frame = Frame(main_notebook, bg=APP_BG_COLOR)
settings_frame = Frame(main_notebook, bg=APP_BG_COLOR)

main_notebook.add(main_app_frame, text='Arama')
main_notebook.add(watch_frame, text='Takip')
main_notebook.add(wishlist_frame, text='Wishlist')
main_notebook.add(settings_frame, text='Ayarlar')

# Search tab
input_frame = LabelFrame(main_app_frame, text='Filtreleme Kriterleri', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR, padx=10, pady=10)
input_frame.pack(padx=10, pady=10, fill='x')
input_frame.grid_columnconfigure(1, weight=1)

Label(input_frame, text='\u00d6\u011fe T\u00fcr\u00fc:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=0,column=0,sticky='w')
item_type_options = ['Fashion','Interior','Jewelry','Hair']
item_type_var = StringVar(value=item_type_options[0])
OptionMenu(input_frame, item_type_var, *item_type_options).grid(row=0,column=1,sticky='ew')

Label(input_frame, text='Para Birimi:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=1,column=0,sticky='w')
currency_type_options = ['1 (Stardollars)','2 (Starcoins)']
currency_type_var = StringVar(value=currency_type_options[0])
OptionMenu(input_frame, currency_type_var, *currency_type_options).grid(row=1,column=1,sticky='ew')

Label(input_frame, text='Min Fiyat:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=2,column=0,sticky='w')
min_price_entry = Entry(input_frame)
min_price_entry.insert(0,'2')
min_price_entry.grid(row=2,column=1,sticky='ew')

Label(input_frame, text='Max Fiyat:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=3,column=0,sticky='w')
max_price_entry = Entry(input_frame)
max_price_entry.insert(0,'600')
max_price_entry.grid(row=3,column=1,sticky='ew')

Label(input_frame, text='Marka Adı:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=4,column=0,sticky='w')
sorted_brand_names = sorted([n for n in BRAND_IDS.keys() if n and 'Se\u00e7iniz' not in n])
display_brand_options = ['Se\u00e7iniz (T\u00fcm Markalar)'] + sorted_brand_names
brand_name_var = StringVar()
brand_name_var.set(display_brand_options[0])
brand_entry = AutocompleteEntry(input_frame, display_brand_options, textvariable=brand_name_var)
brand_entry.grid(row=4,column=1,sticky='ew')

Label(input_frame, text='Anahtar Kelime:', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).grid(row=5,column=0,sticky='w')
keyword_entry = Entry(input_frame)
keyword_entry.grid(row=5,column=1,sticky='ew')

btn_frame = Frame(input_frame, bg=FRAME_BG_COLOR)
btn_frame.grid(row=6,column=0,columnspan=2,pady=10)
search_button = Button(btn_frame, text='Ara', command=start_search_thread, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR)
search_button.pack(side='left', padx=5)
pause_resume_button = Button(btn_frame, text='Duraklat', command=pause_resume_search, state='disabled', bg='#FF8C00', fg='white')
pause_resume_button.pack(side='left', padx=5)
reset_button = Button(btn_frame, text='Sıfırla', command=reset_application, bg='#DC143C', fg='white')
reset_button.pack(side='left', padx=5)

status_label = Label(input_frame, text='Hazır', bg=FRAME_BG_COLOR, fg='green')
status_label.grid(row=7,column=0,columnspan=2)

progress = ttk.Progressbar(main_app_frame, length=400)
progress.pack(pady=5)

output_main = LabelFrame(main_app_frame, text='Sonu\u00e7lar', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR, padx=10,pady=10)
output_main.pack(padx=10,pady=10,fill='both',expand=True)
results_frame = ScrollableFrame(output_main)
results_frame.pack(fill='both', expand=True)

# Watchlist tab
watchlist_box = Listbox(watch_frame)
watchlist_box.pack(fill='both', expand=True, padx=10, pady=10)

# Wishlist tab
wl_input = Entry(wishlist_frame)
wl_input.pack(pady=5)
Button(wishlist_frame, text='Ekle', command=lambda: add_to_wishlist(wl_input.get()), bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR).pack()
wishlist_box = Listbox(wishlist_frame)
wishlist_box.pack(fill='both', expand=True, padx=10, pady=10)
Button(wishlist_frame, text='Se\u00e7ili Sil', command=remove_selected_wishlist).pack(pady=5)

# Settings tab
Button(settings_frame, text='\u00c7erezleri Yeniden Gir', command=refresh_cookies).pack(pady=5)
Button(settings_frame, text='Kay\u0131tl\u0131 \u00c7erezleri Sil', command=clear_saved_cookies).pack(pady=5)
Button(settings_frame, text='Arkaplan Rengi', command=lambda: choose_color('APP_BG_COLOR', root)).pack(pady=5)

# Cookie input frame
cookie_input_frame = Frame(root, bg=FRAME_BG_COLOR, bd=2, relief='groove')
Label(cookie_input_frame, text='Stardoll Oturum \u00c7erezlerinizi Girin', bg=FRAME_BG_COLOR, fg=LABEL_TEXT_COLOR).pack(pady=10)
cookie_entries = {}
for name in ['OAID','pdhUser','SDIT','SESSID','vc']:
    row = Frame(cookie_input_frame, bg=FRAME_BG_COLOR)
    row.pack(fill='x', padx=20, pady=2)
    Label(row, text=f"{name}:", width=10, anchor='e', bg=FRAME_BG_COLOR).pack(side='left')
    ent = Entry(row, width=60)
    ent.pack(side='left', fill='x', expand=True)
    cookie_entries[name] = ent

def show_main_app():
    cookie_input_frame.pack_forget()
    main_notebook.pack(fill='both', expand=True)

def save_and_show_main_app():
    global YOUR_STARDOLL_COOKIES
    entered = {n: e.get().strip() for n,e in cookie_entries.items()}
    YOUR_STARDOLL_COOKIES = entered
    save_encrypted_cookies(entered)
    show_main_app()

Button(cookie_input_frame, text='Kaydet ve Devam Et', command=save_and_show_main_app, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR).pack(pady=20)

saved = load_decrypted_cookies()
if saved and check_cookies(saved):
    YOUR_STARDOLL_COOKIES = saved
    show_main_app()
else:
    cookie_input_frame.pack(fill='both', expand=True, padx=20, pady=20)

root.mainloop()
