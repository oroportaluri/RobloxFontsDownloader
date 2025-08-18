import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import zipfile
import shutil
import ctypes
from ctypes import wintypes
import tempfile
import json
import re

# Fix DPI scaling on Windows
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Make DPI aware
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Fallback for older Windows
        except:
            pass

class FontDownloader:
    def __init__(self):
        self.config = self.load_config()
        self.fonts = list(self.config['fonts'].keys())

        # Create downloads folder
        self.downloads_dir = os.path.join(os.getcwd(), "downloaded_fonts")
        os.makedirs(self.downloads_dir, exist_ok=True)

        self.root = None
        self.progress_var = None
        self.status_label = None
        self.progress_bar = None
        self.success_count = 0
        self.failed_fonts = []

    def load_config(self):
        try:
            # Handle PyInstaller bundled resources
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                config_path = os.path.join(sys._MEIPASS, 'config.json')
            else:
                # Running as script
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Fallback to hardcoded fonts if config fails
            return {
                "fonts": {
                    "Roboto": {"display_name": "Roboto", "urls": ["https://fonts.google.com/download?family=Roboto"]},
                    "Nunito": {"display_name": "Nunito", "urls": ["https://fonts.google.com/download?family=Nunito"]},
                    "Ubuntu": {"display_name": "Ubuntu", "urls": ["https://fonts.google.com/download?family=Ubuntu"]},
                }
            }

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Roblox Fonts Downloader")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        # Center the window
        self.root.eval('tk::PlaceWindow . center')

        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Roblox Fonts Downloader",
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(main_frame, text="Click 'Download Fonts' to begin")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                          maximum=len(self.fonts), length=300)
        self.progress_bar.grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))

        # Download button
        download_btn = ttk.Button(main_frame, text="Download Fonts",
                                command=self.start_download)
        download_btn.grid(row=3, column=0, pady=(0, 5), sticky=tk.W)

        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=self.root.quit)
        close_btn.grid(row=3, column=1, pady=(0, 5), sticky=tk.E)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def get_font_urls_from_css(self, css_url):
        """Extract actual font file URLs from CSS"""
        try:
            response = requests.get(css_url, timeout=15)
            if response.status_code != 200:
                return []

            css_content = response.text

            # Extract URLs from CSS using regex
            url_pattern = r'src:\s*url\(([^)]+)\)'
            urls = re.findall(url_pattern, css_content)

            # Filter for TTF, OTF, WOFF2 files
            font_urls = []
            for url in urls:
                url = url.strip('\'"')
                if any(ext in url.lower() for ext in ['.ttf', '.otf', '.woff2', '.woff']):
                    font_urls.append(url)

            return font_urls
        except:
            return []

    def download_font(self, font_key):
        font_config = self.config['fonts'][font_key]
        display_name = font_config['display_name']
        urls = font_config['urls']

        print(f"\n{display_name}:")
        last_error = None

        # Try each URL source
        for url in urls:
            try:
                if 'css' in url:
                    # CSS endpoint - extract actual font URLs
                    font_urls = self.get_font_urls_from_css(url)
                    if not font_urls:
                        continue

                    # Download and install each font file
                    installed_any = False
                    for font_url in font_urls:
                        try:
                            font_response = requests.get(font_url, timeout=30)
                            font_response.raise_for_status()

                            # Determine file extension
                            if '.ttf' in font_url.lower():
                                ext = '.ttf'
                            elif '.otf' in font_url.lower():
                                ext = '.otf'
                            elif '.woff2' in font_url.lower():
                                ext = '.woff2'
                            elif '.woff' in font_url.lower():
                                ext = '.woff'
                            else:
                                ext = '.ttf'  # default

                            # Save font file to downloads folder
                            font_filename = f"{display_name.replace(' ', '_')}_{len(font_urls)}_{ext.replace('.', '')}"
                            if len(font_urls) > 1:
                                font_filename = f"{display_name.replace(' ', '_')}_variant_{font_urls.index(font_url)+1}{ext}"
                            else:
                                font_filename = f"{display_name.replace(' ', '_')}{ext}"

                            font_save_path = os.path.join(self.downloads_dir, font_filename)

                            with open(font_save_path, 'wb') as f:
                                f.write(font_response.content)

                            print(f"  Downloaded: {font_filename} ({len(font_response.content)} bytes)")

                            # Install font (TTF/OTF only, skip WOFF)
                            if ext in ['.ttf', '.otf']:
                                if self.install_font(font_save_path):
                                    print(f"  Installed: {font_filename}")
                                installed_any = True

                        except Exception as e:
                            print(f"Failed to download font file {font_url}: {str(e)}")
                            continue

                    if installed_any:
                        return True

                else:
                    # Direct download URL (ZIP or TTF/OTF file)
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()

                    # Check if it's a ZIP file
                    if response.content[:2] == b'PK' or 'zip' in response.headers.get('content-type', '').lower():
                        # Create temporary file for the zip
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                            temp_file.write(response.content)
                            temp_zip_path = temp_file.name

                        # Extract and install fonts
                        try:
                            with tempfile.TemporaryDirectory() as temp_dir:
                                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                                    zip_ref.extractall(temp_dir)

                                # Find and install TTF files
                                font_files = []
                                for root, dirs, files in os.walk(temp_dir):
                                    for file in files:
                                        if file.lower().endswith(('.ttf', '.otf')):
                                            font_files.append(os.path.join(root, file))

                                if font_files:
                                    for font_file in font_files:
                                        # Save to downloads folder
                                        font_filename = f"{display_name.replace(' ', '_')}_{os.path.basename(font_file)}"
                                        font_save_path = os.path.join(self.downloads_dir, font_filename)
                                        shutil.copy2(font_file, font_save_path)
                                        print(f"  Downloaded: {font_filename} ({os.path.getsize(font_save_path)} bytes)")

                                        # Install font
                                        if self.install_font(font_save_path):
                                            print(f"  Installed: {font_filename}")
                                    return True
                        except Exception as zip_error:
                            print(f"    ZIP extraction failed: {zip_error}")

                        # Clean up temp zip file
                        try:
                            os.unlink(temp_zip_path)
                        except:
                            pass
                    else:
                        # Direct font file
                        print(f"    Detected direct font file")
                        if url.lower().endswith(('.ttf', '.otf')):
                            ext = '.ttf' if '.ttf' in url.lower() else '.otf'
                            font_filename = f"{display_name.replace(' ', '_')}{ext}"
                            font_save_path = os.path.join(self.downloads_dir, font_filename)

                            with open(font_save_path, 'wb') as f:
                                f.write(response.content)

                            print(f"    Saved: {font_filename}")
                            self.install_font(font_save_path)
                            return True
                        else:
                            print(f"    Unknown file type for URL: {url}")
                            continue

            except Exception as e:
                last_error = e
                print(f"Failed URL {url} for {display_name}: {str(e)}")
                continue

        # If we get here, all URLs failed
        print(f"Error downloading {display_name}: All URLs failed. Last error: {str(last_error)}")
        return False

    def install_font(self, font_path):
        try:
            # Windows font installation
            if sys.platform == "win32":
                # Get the Windows fonts directory
                fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')

                # Copy font to fonts directory
                font_name = os.path.basename(font_path)
                dest_path = os.path.join(fonts_dir, font_name)

                # Only copy if it doesn't exist
                if not os.path.exists(dest_path):
                    shutil.copy2(font_path, dest_path)

                # Register the font with Windows
                return self.register_font(dest_path)
            return False

        except Exception as e:
            print(f"  Error installing font: {str(e)}")
            return False

    def register_font(self, font_path):
        """
        Improved font registration using Windows API best practices
        """
        try:
            import winreg

            # Constants
            FONTS_REG_PATH = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D

            # Setup Windows API calls with proper types
            gdi32 = ctypes.windll.gdi32
            user32 = ctypes.windll.user32

            gdi32.AddFontResourceW.argtypes = [wintypes.LPCWSTR]
            gdi32.AddFontResourceW.restype = ctypes.c_int

            user32.SendMessageTimeoutW.argtypes = [
                wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                ctypes.POINTER(wintypes.DWORD)
            ]

            # Load the font resource
            result = gdi32.AddFontResourceW(font_path)

            if result > 0:
                # Determine font type and create proper registry entry
                font_filename = os.path.basename(font_path)
                font_name_no_ext = os.path.splitext(font_filename)[0]
                font_extension = os.path.splitext(font_filename)[1].lower()

                # Determine font type for registry
                if font_extension == '.ttf':
                    font_type = '(TrueType)'
                elif font_extension == '.otf':
                    font_type = '(OpenType)'
                else:
                    font_type = '(TrueType)'  # Default fallback

                registry_name = f"{font_name_no_ext} {font_type}"

                # Add to Windows registry for permanent installation
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, FONTS_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, registry_name, 0, winreg.REG_SZ, font_filename)
                except PermissionError:
                    pass  # Silent fail on permission errors
                except Exception:
                    pass  # Silent fail on other registry errors

                # Notify system with timeout to prevent hanging
                try:
                    timeout_result = wintypes.DWORD()
                    user32.SendMessageTimeoutW(
                        HWND_BROADCAST, WM_FONTCHANGE, 0, 0,
                        0, 1000, ctypes.byref(timeout_result)  # 1 second timeout
                    )
                except Exception:
                    # Fallback to simple SendMessage
                    user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

                return True
            else:
                return False

        except Exception as e:
            print(f"Error registering font {font_path}: {str(e)}")
            return False

    def download_fonts_thread(self):
        self.success_count = 0
        self.failed_fonts = []

        for i, font_key in enumerate(self.fonts):
            font_config = self.config['fonts'][font_key]
            display_name = font_config['display_name']

            self.root.after(0, lambda name=display_name: self.status_label.config(
                text=f"Downloading {name}..."))

            success = self.download_font(font_key)

            if success:
                self.success_count += 1
            else:
                self.failed_fonts.append(display_name)

            # Update progress bar
            self.root.after(0, lambda: self.progress_var.set(i + 1))

        # Show completion message
        self.root.after(0, self.show_completion_message)

    def show_completion_message(self):
        total_fonts = len(self.fonts)
        failed_count = len(self.failed_fonts)

        # Console output summary
        print("\n" + "="*50)
        print("INSTALLATION COMPLETE!")
        print("="*50)
        print(f"✅ Successfully installed: {self.success_count}/{total_fonts} fonts")

        if self.failed_fonts:
            print(f"❌ Failed: {len(self.failed_fonts)} fonts")

        print(f"\nFiles saved to: {self.downloads_dir}")
        print("\nFonts are now available in all applications!")
        print("="*50)

        # GUI message
        if failed_count == 0:
            message = (f"✅ Success! All {total_fonts} fonts have been downloaded and installed.\n\n"
                      f"Font files saved to: {self.downloads_dir}\n\n"
                      f"Check the console window for detailed installation info.")
            title = "Download Complete"
            messagebox.showinfo(title, message)
        else:
            message = (f"⚠️ Download completed with some issues:\n\n"
                      f"✅ Successfully installed: {self.success_count} fonts\n"
                      f"❌ Failed to install: {failed_count} fonts\n\n"
                      f"Font files saved to: {self.downloads_dir}\n\n"
                      f"Check the console window for detailed installation info.")

            if failed_count <= 5:  # Show failed fonts if not too many
                message += f"\n\nFailed fonts:\n" + "\n".join(self.failed_fonts)

            title = "Download Complete (with errors)"
            messagebox.showwarning(title, message)

        self.status_label.config(text="Download completed! You can close this window.")

    def start_download(self):
        # Disable the download button
        for widget in self.root.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button) and child.cget('text') == 'Download Fonts':
                    child.config(state='disabled')

        # Start download in a separate thread
        download_thread = threading.Thread(target=self.download_fonts_thread)
        download_thread.daemon = True
        download_thread.start()

    def run(self):
        self.setup_gui()
        self.root.mainloop()

def request_admin_privileges():
    """Request administrator privileges by re-launching the script with elevated permissions"""
    try:
        if sys.platform == "win32":
            import subprocess
            # Determine if we're running from an executable or script
            if getattr(sys, 'frozen', False):
                # Running from PyInstaller executable
                executable_path = sys.executable
                subprocess.run([
                    'powershell', '-Command',
                    f'Start-Process "{executable_path}" -Verb RunAs'
                ], check=True)
            else:
                # Running from Python script
                subprocess.run([
                    'powershell', '-Command',
                    f'Start-Process python -ArgumentList "{os.path.abspath(__file__)}" -Verb RunAs'
                ], check=True)
            return True
    except Exception as e:
        print(f"Failed to request admin privileges: {e}")
        return False
    return False

if __name__ == "__main__":
    try:
        # Check if running as admin on Windows
        if sys.platform == "win32":
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            except:
                is_admin = False

            if not is_admin:
                print("Administrator privileges required. Attempting to restart with elevated permissions...")
                if request_admin_privileges():
                    print("Restarting with administrator privileges...")
                    sys.exit(0)
                else:
                    print("Failed to request administrator privileges.")
                    print("Please manually run this application as administrator.")
                    if not getattr(sys, 'frozen', False):  # Only wait for input if running as script
                        input("Press Enter to exit...")
                    sys.exit(1)

        print("="*60)
        print("ROBLOX FONTS DOWNLOADER")
        print("="*60)
        print("Starting application...")

        app = FontDownloader()
        app.run()

        # Wait for user input before closing (only for executable)
        if getattr(sys, 'frozen', False):
            input("\nPress Enter to exit...")

    except Exception as e:
        # Handle any startup errors
        error_msg = f"Application failed to start:\n\n{str(e)}\n\nCurrent directory: {os.getcwd()}"

        try:
            # Try to show error in GUI
            import tkinter.messagebox as msgbox
            error_root = tkinter.Tk()
            error_root.withdraw()  # Hide the main window
            msgbox.showerror("Startup Error", error_msg)
            error_root.destroy()
        except:
            # If GUI fails, write to error log
            try:
                with open("error_log.txt", "w") as f:
                    f.write(f"Startup Error: {str(e)}\n")
                    f.write(f"Current directory: {os.getcwd()}\n")
                    try:
                        f.write(f"Files in directory: {os.listdir('.')}\n")
                    except:
                        f.write("Could not list directory contents\n")
                print(f"Error logged to error_log.txt: {str(e)}")
            except:
                print(f"Critical error: {str(e)}")

        sys.exit(1)
