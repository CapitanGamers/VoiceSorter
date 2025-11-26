import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import numpy as np

missing_libs = []
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
except ImportError:
    missing_libs.append("ttkbootstrap")
try:
    import librosa
except ImportError:
    missing_libs.append("librosa")
try:
    import soundfile
except ImportError:
    missing_libs.append("soundfile")
try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
except ImportError:
    missing_libs.append("scikit-learn")

if missing_libs:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("خطا", f"لطفاً نصب کنید:\npip install {' '.join(missing_libs)}")
    raise SystemExit


FONT_NAME = "Vazirmatn" 
FONT_NORMAL = (FONT_NAME, 10)
FONT_BOLD = (FONT_NAME, 11, "bold")
FONT_HEADER = (FONT_NAME, 16, "bold")

class SplashApp:
    def __init__(self, root, main_app_callback):
        self.root = root
        self.callback = main_app_callback
        
        
        width, height = 500, 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.splash = tk.Toplevel(root)
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
        self.splash.overrideredirect(True) 
        self.splash.configure(bg="#2b2d30")
        frame = tk.Frame(self.splash, bg="#2b2d30")
        frame.pack(expand=True, fill='both')
        lbl = tk.Label(frame, text="با احترام به صابر راستی کردار", 
                       font=(FONT_NAME, 18, "bold"), fg="white", bg="#2b2d30")
        lbl.pack(expand=True)
        self.root.after(2500, self.start_fade_out)

    def start_fade_out(self):
        alpha = 1.0
        self.fade_step(alpha)

    def fade_step(self, alpha):
        if alpha > 0:
            alpha -= 0.05
            self.splash.attributes("-alpha", alpha)
            self.root.after(30, lambda: self.fade_step(alpha))
        else:
            self.splash.destroy()
            self.callback()

class AudioSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Sorter")
        self.root.geometry("800x720")
        
        
        style = ttk.Style()
        style.configure('.', font=FONT_NORMAL)
        style.configure('TButton', font=FONT_NORMAL)
        style.configure('TLabelframe.Label', font=FONT_BOLD)
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.sample_files = []

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=BOTH, expand=True)

        header = ttk.Label(main_frame, text="دسته‌بندی فایل‌های صوتی", font=FONT_HEADER, bootstyle="primary")
        header.pack(pady=(0, 25), anchor="center")

        frame_paths = ttk.Labelframe(main_frame, text=" مسیر فایل‌ها ", padding="15", bootstyle="secondary")
        frame_paths.pack(fill=X, pady=10)

        r1 = ttk.Frame(frame_paths)
        r1.pack(fill=X, pady=5)
        self.entry_input = ttk.Entry(r1, textvariable=self.input_dir, state="readonly", justify="right")
        self.entry_input.pack(side=RIGHT, fill=X, expand=True, padx=(10, 0))
        ttk.Button(r1, text="انتخاب ورودی", command=self.select_input, bootstyle="secondary-outline", width=15).pack(side=RIGHT)

        r2 = ttk.Frame(frame_paths)
        r2.pack(fill=X, pady=5)
        self.entry_output = ttk.Entry(r2, textvariable=self.output_dir, state="readonly", justify="right")
        self.entry_output.pack(side=RIGHT, fill=X, expand=True, padx=(10, 0))
        ttk.Button(r2, text="انتخاب خروجی", command=self.select_output, bootstyle="secondary-outline", width=15).pack(side=RIGHT)

        frame_samples = ttk.Labelframe(main_frame, text=" فیلتر گوینده خاص (اختیاری) ", padding="15", bootstyle="secondary")
        frame_samples.pack(fill=X, pady=10)
        
        r3 = ttk.Frame(frame_samples)
        r3.pack(fill=X, pady=5)
        
        ttk.Button(r3, text="انتخاب نمونه صدا", command=self.select_samples, bootstyle="warning-outline", width=15).pack(side=RIGHT)
        self.lbl_samples = ttk.Label(r3, text="برای جداسازی یک فرد خاص، ۱ تا ۳ نمونه از صدای او را انتخاب کنید", bootstyle="secondary", font=(FONT_NAME, 9))
        self.lbl_samples.pack(side=RIGHT, padx=(0, 10))

        self.btn_start = ttk.Button(main_frame, text="اجرای عملیات", command=self.start_thread, bootstyle="success", padding=12)
        self.btn_start.pack(fill=X, pady=20)
        
        frame_log = ttk.Frame(main_frame)
        frame_log.pack(fill=BOTH, expand=True)

        self.status_label = ttk.Label(frame_log, text="آماده", font=(FONT_NAME, 10), anchor="e")
        self.status_label.pack(fill=X)
        
        self.progress = ttk.Progressbar(frame_log, bootstyle="success-striped", length=100)
        self.progress.pack(fill=X, pady=(5, 10))
        
        self.log_box = scrolledtext.ScrolledText(frame_log, height=8, bg="#2b2d30", fg="#bdc3c7", 
                                               insertbackground="white", relief="flat", font=(FONT_NAME, 10))
        self.log_box.tag_config('rtl', justify='right') # تنظیم راست‌چین برای متن لاگ
        self.log_box.pack(fill=BOTH, expand=True)

    def log(self, msg):
        self.root.after(0, lambda: self._log_update(msg))
    
    def _log_update(self, msg):
        self.log_box.insert(tk.END, msg + "\n", 'rtl')
        self.log_box.see(tk.END)

    def select_input(self):
        path = filedialog.askdirectory()
        if path: self.input_dir.set(path)

    def select_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)

    def select_samples(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.wav *.mp3 *.flac *.m4a")])
        if files:
            self.sample_files = list(files)[:3]
            self.lbl_samples.config(text=f"{len(self.sample_files)} فایل نمونه انتخاب شد", bootstyle="warning")
            self.log("نمونه صدا دریافت شد.")

    def start_thread(self):
        self.log_box.delete('1.0', tk.END)
        threading.Thread(target=self.process, daemon=True).start()

    def update_progress(self, value, text):
        self.root.after(0, lambda: self._update_progress_ui(value, text))

    def _update_progress_ui(self, value, text):
        self.progress['value'] = value
        self.status_label.config(text=text)

    def extract_features(self, file_path):
        try:
            y, sr = librosa.load(file_path, duration=40, sr=None)
            y_trimmed, _ = librosa.effects.trim(y, top_db=25)
            if len(y_trimmed) < sr: y_trimmed = y
            
            mfcc = librosa.feature.mfcc(y=y_trimmed, sr=sr, n_mfcc=40)
            mfcc_delta = librosa.feature.delta(mfcc)
            
            mean_mfcc = np.mean(mfcc, axis=1)
            std_mfcc = np.std(mfcc, axis=1)
            mean_delta = np.mean(mfcc_delta, axis=1)
            std_delta = np.std(mfcc_delta, axis=1)
            
            return np.hstack([mean_mfcc, std_mfcc, mean_delta, std_delta])
        except Exception as e:
            return None

    def process(self):
        inp, out = self.input_dir.get(), self.output_dir.get()
        if not inp or not out:
            self.log("خطا: پوشه ورودی یا خروجی انتخاب نشده است.")
            return

        self.btn_start.config(state="disabled")
        
        try:
            all_files = [f for f in os.listdir(inp) if f.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg'))]
            if not all_files:
                self.log("فایلی یافت نشد.")
                self.btn_start.config(state="normal")
                return

            features = []
            valid_files = []
            total = len(all_files)
            
            for idx, f in enumerate(all_files):
                perc = ((idx + 1) / total) * 90
                self.update_progress(perc, f"پردازش: {f}")
                feat = self.extract_features(os.path.join(inp, f))
                if feat is not None:
                    features.append(feat)
                    valid_files.append(f)

            if not features:
                self.log("خطا در استخراج ویژگی‌ها.")
                return
            
            self.update_progress(95, "دسته‌بندی...")
            X = np.array(features)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=45, metric='euclidean', linkage='ward')
            labels = clustering.fit_predict(X_scaled)
            
            target_label = -1
            if self.sample_files:
                self.log("تطبیق با نمونه...")
                sample_feats = []
                for sf in self.sample_files:
                    sf_feat = self.extract_features(sf)
                    if sf_feat is not None: sample_feats.append(sf_feat)
                
                if sample_feats:
                    target_vector = np.mean(scaler.transform(np.array(sample_feats)), axis=0)
                    min_dist = float('inf')
                    for lbl in set(labels):
                        cluster_mean = np.mean(X_scaled[labels == lbl], axis=0)
                        dist = np.linalg.norm(target_vector - cluster_mean)
                        if dist < min_dist:
                            min_dist = dist
                            target_label = lbl
                    self.log(f"هدف در گروه {target_label} شناسایی شد.")

            self.update_progress(98, "انتقال فایل‌ها...")
            counts = {}
            for filename, label in zip(valid_files, labels):
                folder_name = "Target_Speaker" if label == target_label else f"Group_{label}"
                target_path = os.path.join(out, folder_name)
                os.makedirs(target_path, exist_ok=True)
                try:
                    shutil.copy2(os.path.join(inp, filename), os.path.join(target_path, filename))
                    counts[folder_name] = counts.get(folder_name, 0) + 1
                except: pass

            self.update_progress(100, "پایان.")
            self.log("-" * 20)
            for k, v in counts.items():
                self.log(f"پوشه {k}: {v} فایل")
            
            messagebox.showinfo("پایان", "عملیات انجام شد.")

        except Exception as e:
            self.log(f"خطا: {e}")
        finally:
            self.btn_start.config(state="normal")
            self.update_progress(0, "آماده")

def main_program():
    root.deiconify()

if __name__ == "__main__":
   
    root = ttk.Window(themename="superhero")
    root.withdraw()
    
    app = AudioSorterApp(root)
    
    splash = SplashApp(root, main_program)
    
    root.mainloop()
