import tkinter as tk
from tkinter import ttk
import colorsys
import pyperclip
import platform
import os
import sys
from PIL import ImageGrab, Image
import time

# グローバル変数として先に定義
default_steps = 8
default_step_size = 5
is_eyedropper_active = False  # スポイトモードの状態管理用

# グローバル変数として UI 要素を定義
root = None
input_frame = None
color_frame = None
color_canvas = None
hue_entry = None
sat_entry = None
val_entry = None
step_entry = None
steps_entry = None
eyedropper_button = None

def create_gui():
    global root, input_frame, color_frame, color_canvas, hue_entry, sat_entry
    global val_entry, step_entry, steps_entry, eyedropper_button

    # GUIアプリケーションの設定
    root = tk.Tk()
    root.title("HSV Color Display with HEX Copy")

    # ESCキーでスポイトモードをキャンセル
    root.bind('<Escape>', lambda e: cancel_eyedropper())

    # アイコンの設定
    icon_path = resource_path('app_icon.ico')
    if os.path.exists(icon_path):
        try:
            if platform.system() == 'Windows':
                root.iconbitmap(icon_path)
            else:
                # 他のOSではiconphotoを使用
                img = tk.PhotoImage(file=icon_path)
                root.iconphoto(False, img)
        except Exception as e:
            print(f"アイコンの設定中にエラーが発生しました: {e}")
    else:
        print("アイコンファイルが見つかりません。")

    # デフォルトウィンドウのサイズ設定
    color_display_height = default_steps * 30 + 20  # パディングを追加
    root.geometry(f"680x{color_display_height + 150}")

    # 左側（入力部分）
    input_frame = tk.Frame(root)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    # 入力フィールド
    hue_label = tk.Label(input_frame, text="Hue (0-360):")
    hue_label.grid(row=0, column=0, padx=2, pady=2, sticky="e")
    hue_entry = tk.Entry(input_frame, width=10)
    hue_entry.grid(row=0, column=1, padx=2, pady=2)

    sat_label = tk.Label(input_frame, text="Saturation (0-255):")
    sat_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")
    sat_entry = tk.Entry(input_frame, width=10)
    sat_entry.grid(row=1, column=1, padx=2, pady=2)

    val_label = tk.Label(input_frame, text="Value (0-255):")
    val_label.grid(row=2, column=0, padx=2, pady=2, sticky="e")
    val_entry = tk.Entry(input_frame, width=10)
    val_entry.grid(row=2, column=1, padx=2, pady=2)

    step_label = tk.Label(input_frame, text="減少ステップ:")
    step_label.grid(row=3, column=0, padx=2, pady=2, sticky="e")
    step_entry = tk.Entry(input_frame, width=10)
    step_entry.grid(row=3, column=1, padx=2, pady=2)
    step_entry.insert(0, str(default_step_size))

    steps_label = tk.Label(input_frame, text="ステップ数:")
    steps_label.grid(row=4, column=0, padx=2, pady=2, sticky="e")
    steps_entry = tk.Entry(input_frame, width=10)
    steps_entry.grid(row=4, column=1, padx=2, pady=2)
    steps_entry.insert(0, str(default_steps))

    # スポイトボタン
    eyedropper_button = tk.Button(input_frame, text="スポイト", command=toggle_eyedropper)
    eyedropper_button.grid(row=5, column=0, columnspan=2, pady=5)

    # 右側（色表示部分）
    color_frame_container = tk.Frame(root)
    color_frame_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # キャンバスとスクロールバー
    global color_canvas
    color_canvas = tk.Canvas(color_frame_container, width=780, height=color_display_height)
    scrollbar = tk.Scrollbar(color_frame_container, orient="vertical", command=color_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")

    color_canvas.pack(side=tk.LEFT, fill="both", expand=True)
    global color_frame
    color_frame = tk.Frame(color_canvas)
    color_canvas.create_window((0, 0), window=color_frame, anchor="nw")

    # スクロールバーとキャンバスの連携
    color_canvas.configure(yscrollcommand=scrollbar.set)

    # 入力値の変更を監視
    for entry in [hue_entry, sat_entry, val_entry, step_entry, steps_entry]:
        entry.bind('<KeyRelease>', lambda e: root.after(100, update_colors))

    # キャンバスにマウスホイールのイベントをバインド
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        color_canvas.bind_all("<MouseWheel>", on_mouse_wheel)
    else:
        color_canvas.bind_all("<Button-4>", on_mouse_wheel)
        color_canvas.bind_all("<Button-5>", on_mouse_wheel)

    # ウィンドウのリサイズに対応するための設定
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    color_frame_container.grid_rowconfigure(0, weight=1)
    color_frame_container.grid_columnconfigure(0, weight=1)

    # 最初の色を表示
    hue_entry.insert(0, "0")
    sat_entry.insert(0, "255")
    val_entry.insert(0, "255")
    update_colors()

# リソースパス関数
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# HSV -> RGB変換
def hsv_to_rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360, s / 255, v / 255)
    return int(r * 255), int(g * 255), int(b * 255)

# RGB -> HEX変換
def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

# RGB -> HSV変換
def rgb_to_hsv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return int(h * 360), int(s * 255), int(v * 255)

# コピー機能
def copy_to_clipboard(value):
    pyperclip.copy(value)

# スポイト機能
def toggle_eyedropper():
    global is_eyedropper_active
    if not is_eyedropper_active:
        is_eyedropper_active = True
        eyedropper_button.config(relief="sunken")  # ボタンを押された状態に
        root.config(cursor="crosshair")  # カーソルを十字に変更
        # クリックイベントをバインド
        root.bind('<Button-1>', pick_color)
        root.attributes('-alpha', 0.5)  # ウィンドウを半透明に
    else:
        cancel_eyedropper()

def cancel_eyedropper():
    global is_eyedropper_active
    is_eyedropper_active = False
    eyedropper_button.config(relief="raised")  # ボタンを通常状態に
    root.config(cursor="")  # カーソルを通常に戻す
    root.unbind('<Button-1>')  # クリックイベントのバインドを解除
    root.attributes('-alpha', 1.0)  # ウィンドウの透明化を解除

def pick_color(event=None):
    global is_eyedropper_active
    if is_eyedropper_active:
        try:
            # マウスの現在位置を取得
            x = root.winfo_pointerx()
            y = root.winfo_pointery()
            
            # スクリーンショットを取得
            screenshot = ImageGrab.grab()
            # マウス位置の色を取得
            color = screenshot.getpixel((x, y))
            
            # RGB値をHSVに変換
            h, s, v = rgb_to_hsv(*color[:3])  # アルファチャンネルがある場合は除外
            
            # 入力欄を更新
            hue_entry.delete(0, tk.END)
            hue_entry.insert(0, str(h))
            sat_entry.delete(0, tk.END)
            sat_entry.insert(0, str(s))
            val_entry.delete(0, tk.END)
            val_entry.insert(0, str(v))
            
            # 色を更新
            update_colors()
            
        except Exception as e:
            print(f"Color picking error: {e}")
        finally:
            cancel_eyedropper()  # スポイトモードを終了

# 色の表示を更新する関数
def update_colors():
    try:
        h = int(hue_entry.get())
        s = int(sat_entry.get())
        v = int(val_entry.get())
        step = int(step_entry.get())
        steps = int(steps_entry.get())

        # 現在表示されているラベルを全て削除
        for widget in color_frame.winfo_children():
            widget.destroy()

        for i in range(steps):
            current_v = v - (i * step)
            if current_v < 0:
                current_v = 0

            rgb = hsv_to_rgb(h, s, current_v)
            hex_color = rgb_to_hex(*rgb)

            # 通し番号
            index_label = tk.Label(color_frame, text=f"{i+1}", width=2, anchor="w")
            index_label.grid(row=i, column=0, padx=(2, 5), pady=2)

            # HSV表示ラベルとコピー
            hsv_text = f"HSV({h}, {s}, {current_v})"
            hsv_copy_text = f"{h}, {s}, {current_v}"
            hsv_label = tk.Label(color_frame, text=hsv_text, anchor="w", width=15)
            hsv_label.grid(row=i, column=1, padx=(2, 5), pady=2)
            hsv_label.bind("<Button-1>", lambda e, h=hsv_copy_text: copy_to_clipboard(h))

            # RGB表示ラベルとコピー
            rgb_text = f"RGB({rgb[0]}, {rgb[1]}, {rgb[2]})"
            rgb_copy_text = f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
            rgb_label = tk.Label(color_frame, text=rgb_text, anchor="w", width=15)
            rgb_label.grid(row=i, column=2, padx=(2, 5), pady=2)
            rgb_label.bind("<Button-1>", lambda e, r=rgb_copy_text: copy_to_clipboard(r))

            # HEX表示ラベルとコピー
            hex_label = tk.Label(color_frame, text=f"{hex_color}", anchor="w", width=10)
            hex_label.grid(row=i, column=3, padx=(2, 5), pady=2)
            hex_label.bind("<Button-1>", lambda e, hx=hex_color: copy_to_clipboard(hx))

            # 色の四角形（枠線なし）
            color_box = tk.Label(color_frame, bg=hex_color, width=10, height=2)
            color_box.grid(row=i, column=4, padx=(2, 5), pady=2)

        # スクロール領域の設定
        color_canvas.update_idletasks()
        color_canvas.configure(scrollregion=color_canvas.bbox("all"))

    except ValueError:
        pass  # 無効な入力があれば無視する

# マウスホイールでスクロールできるように設定
def on_mouse_wheel(event):
    system = platform.system()
    if system == 'Windows':
        color_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    elif system == 'Darwin':  # macOS
        color_canvas.yview_scroll(int(-1*(event.delta)), "units")
    else:  # Linuxなど
        if event.num == 4:
            color_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            color_canvas.yview_scroll(1, "units")

if __name__ == "__main__":
    create_gui()
    root.mainloop()
