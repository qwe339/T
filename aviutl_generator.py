import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import wave
import glob
import re

class CharacterSettings:
    def __init__(self, name: str):
        self.name = name
        self.frame_offset = 0  # フレーム調整値 (0-100)
        self.layer_base = 1    # 開始レイヤー番号
        self.line_length = 0   # 1行の文字数 (0=改行しない)

class AudioFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.character_name = self._get_character_name()
        self.duration = self._get_duration()

    def _get_character_name(self):
        match = re.search(r'\d+_([^_]+)_', os.path.basename(self.file_path))
        return match.group(1) if match else "unknown"

    def _get_duration(self):
        try:
            with wave.open(self.file_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / float(rate)
        except:
            return 0.0

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AviUtl Project Generator')
        self.geometry('500x600')
        self.resizable(False, False)

        self.folder_path = tk.StringVar()
        self.status_var = tk.StringVar(value='待機中')
        self.characters = {}
        self.char_frames = {}

        self.create_widgets()

    def create_widgets(self):
        # フォルダ選択
        folder_frame = ttk.Frame(self, padding=5)
        folder_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(folder_frame, text='WAVファイルのフォルダ:').pack(side='left')
        ttk.Entry(folder_frame, textvariable=self.folder_path).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(folder_frame, text='参照...', command=self.select_folder).pack(side='left')

        # キャラクター設定（スクロール可能）
        settings_frame = ttk.LabelFrame(self, text='キャラクター設定', padding=5)
        settings_frame.pack(fill='both', expand=True, padx=5, pady=5)

        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ステータス表示
        ttk.Label(self, textvariable=self.status_var).pack(pady=5)

        # ボタン
        button_frame = ttk.Frame(self, padding=5)
        button_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(button_frame, text='生成', command=self.generate).pack(side='left', padx=5)
        ttk.Button(button_frame, text='終了', command=self.quit).pack(side='left')

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.update_character_frames(folder)

    def update_character_frames(self, folder_path):
        # 既存のフレームをクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.characters.clear()
        self.char_frames.clear()

        # WAVファイルを収集
        wav_files = glob.glob(os.path.join(folder_path, "*.wav"))
        wav_files.sort(key=lambda x: int(re.search(r'(\d+)_', os.path.basename(x)).group(1)))

        # キャラクター一覧を取得
        characters = set()
        for wav_file in wav_files:
            audio = AudioFile(wav_file)
            characters.add(audio.character_name)

        # キャラクターごとの設定フレームを作成
        for i, char_name in enumerate(sorted(characters)):
            self.characters[char_name] = CharacterSettings(char_name)
            char = self.characters[char_name]
            
            frame = ttk.LabelFrame(self.scrollable_frame, text=char_name)
            frame.pack(fill='x', padx=5, pady=5)

            # フレーム調整
            frame_frame = ttk.Frame(frame)
            frame_frame.pack(fill='x', padx=5, pady=2)
            
            frame_var = tk.IntVar(value=char.frame_offset)
            ttk.Label(frame_frame, text='フレーム調整:').pack(side='left', padx=5)
            tk.Scale(frame_frame, from_=0, to=100, variable=frame_var, orient='horizontal', resolution=1, showvalue=0).pack(side='left', fill='x', expand=True)
            ttk.Entry(frame_frame, textvariable=frame_var, width=5, justify='right').pack(side='left', padx=5)

            # レイヤー設定
            layer_frame = ttk.Frame(frame)
            layer_frame.pack(fill='x', padx=5, pady=2)
            
            layer_var = tk.IntVar(value=i*3 + 1)  # デフォルトは3つずつ
            ttk.Label(layer_frame, text='開始レイヤー:').pack(side='left', padx=5)
            ttk.Entry(layer_frame, textvariable=layer_var, width=5, justify='right').pack(side='left', padx=5)

            # 文字数設定（改行制御）
            line_frame = ttk.Frame(frame)
            line_frame.pack(fill='x', padx=5, pady=2)
            
            line_var = tk.IntVar(value=char.line_length)
            ttk.Label(line_frame, text='1行の文字数 (0=改行しない):').pack(side='left', padx=5)
            ttk.Entry(line_frame, textvariable=line_var, width=5, justify='right').pack(side='left', padx=5)

            # 値の変更をキャラクター設定に反映
            def update_frame(var, char):
                try:
                    char.frame_offset = max(0, min(100, int(var.get())))
                except:
                    pass

            def update_layer(var, char):
                try:
                    char.layer_base = max(1, int(var.get()))
                except:
                    pass

            def update_line_length(var, char):
                try:
                    char.line_length = max(0, int(var.get()))
                except:
                    pass

            frame_var.trace_add('write', lambda *args, v=frame_var, c=char: update_frame(v, c))
            layer_var.trace_add('write', lambda *args, v=layer_var, c=char: update_layer(v, c))
            line_var.trace_add('write', lambda *args, v=line_var, c=char: update_line_length(v, c))

            self.char_frames[char_name] = {
                'frame': frame,
                'frame_value': frame_var,
                'layer_value': layer_var,
                'line_value': line_var
            }

    def generate(self):
        folder_path = self.folder_path.get()
        if not folder_path:
            messagebox.showerror('エラー', 'フォルダを選択してください')
            return

        try:
            output_path = os.path.join(folder_path, os.path.basename(folder_path) + '.exo')
            if self.create_exo_file(output_path):
                self.status_var.set('完了')
                messagebox.showinfo('完了', f'EXOファイルを生成しました:\n{output_path}')
            else:
                self.status_var.set('エラーが発生しました')
        except Exception as e:
            self.status_var.set('エラーが発生しました')
            messagebox.showerror('エラー', str(e))

    def create_exo_file(self, output_path):
        try:
            # WAVファイルを収集
            wav_files = glob.glob(os.path.join(os.path.dirname(output_path), "*.wav"))
            wav_files.sort(key=lambda x: int(re.search(r'(\d+)_', os.path.basename(x)).group(1)))
            
            # フレーム位置を計算
            current_frame = 1
            positions = []
            total_length = 0

            for wav_path in wav_files:
                audio = AudioFile(wav_path)
                char = self.characters[audio.character_name]
                
                length = int(audio.duration * 30 + 0.5)
                end = current_frame + length - 1
                positions.append((current_frame, end, audio))
                total_length = max(total_length, end)
                current_frame = end + 1 + char.frame_offset

            # EXOファイル生成
            content = [self.create_header(total_length)]
            
            for i, (start, end, audio) in enumerate(positions):
                char = self.characters[audio.character_name]
                content.extend(self.create_object_sections(audio, start, end, i, char))

            # ファイル書き込み
            with open(output_path, 'w', encoding='cp932', errors='replace') as f:
                f.write('\r\n\r\n'.join(content))

            return True
        except Exception as e:
            messagebox.showerror('エラー', str(e))
            return False

    def create_header(self, length):
        return f"""[exedit]
width=1920
height=1080
rate=30
scale=1
length={length}
audio_rate=44100
audio_ch=2"""

    def create_object_sections(self, audio, start, end, index, char):
        base = index * 3
        group = index + 1
        escaped_path = audio.file_path.replace('\\', '\\\\')

        sections = [
            # 音声セクション
            f"""[{base}]
start={start}
end={end}
layer={char.layer_base}
group={group}
overlay=1
audio=1
[{base}.0]
_name=音声ファイル
再生位置=0.00
再生速度=100.0
ループ再生=0
動画ファイルと連携=0
file={escaped_path}
[{base}.1]
_name=標準再生
音量=100.0
左右=0.0""",

            # 口パクセクション
            f"""[{base + 1}]
start={start}
end={end}
layer={char.layer_base + 1}
group={group}
overlay=1
camera=0
[{base + 1}.0]
_name=カスタムオブジェクト
track0=0.00
track1=0.00
track2=0.00
track3=0.00
check0=0
type=0
filter=2
name=口パク準備@PSDToolKit
param=file="{escaped_path}"
[{base + 1}.1]
_name=標準描画
X=0.0
Y=0.0
Z=0.0
拡大率=100.0
透明度=100.0
回転=0.00
blend=0""",

            # テキストセクション
            f"""[{base + 2}]
start={start}
end={end}
layer={char.layer_base + 2}
group={group}
overlay=1
camera=0
[{base + 2}.0]
_name=テキスト
サイズ=1
表示速度=0.0
文字毎に個別オブジェクト=0
移動座標上に表示する=0
自動スクロール=0
B=0
I=0
type=0
autoadjust=0
soft=0
monospace=0
align=4
spacing_x=0
spacing_y=0
precision=0
color=ffffff
color2=000000
font=MS UI Gothic
text={self.get_text_content(audio.file_path, char)}
[{base + 2}.1]
_name=標準描画
X=0.0
Y=50.0
Z=0.0
拡大率=100.0
透明度=100.0
回転=0.00
blend=0"""]

        return sections

    def get_text_content(self, wav_path, char):
        txt_path = wav_path.rsplit('.', 1)[0] + '.txt'
        text = self.read_text_file(txt_path)
        
        # line_length が 0 より大きい場合のみ改行処理を行う
        if char.line_length > 0:
            lines = []
            current_line = []
            current_length = 0
            
            for c in text:
                if c == '\n':
                    lines.append(''.join(current_line))
                    current_line = []
                    current_length = 0
                else:
                    current_line.append(c)
                    current_length += 1
                    if current_length >= char.line_length:
                        lines.append(''.join(current_line))
                        current_line = []
                        current_length = 0
            
            if current_line:
                lines.append(''.join(current_line))
            
            formatted_text = '\n'.join(lines)
        else:
            # 改行しない場合は元のテキストをそのまま使用
            formatted_text = text

        script = f'<?s=[==[\n{formatted_text}\n]==];require("PSDToolKit").subtitle:set(s,obj,true);s=nil?>'
        return script.encode('utf-16le').hex().ljust(4096, '0')

    def read_text_file(self, txt_path):
        encodings = ['utf-8', 'shift_jis', 'cp932']
        for encoding in encodings:
            try:
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding=encoding) as f:
                        text = f.read().strip()
                        if text.startswith('\ufeff'):
                            text = text[1:]
                        return text
            except:
                continue
        return ""

if __name__ == '__main__':
    app = Application()
    app.mainloop()