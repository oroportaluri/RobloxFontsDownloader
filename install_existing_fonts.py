#!/usr/bin/env python3
"""
Quick script to manually install the already downloaded fonts.
Run this with admin privileges.
"""

import os
import sys
import ctypes
import winreg
import shutil
from ctypes import wintypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_font(font_path):
    """Install a single font file with proper Windows API handling"""
    if not os.path.exists(font_path):
        print(f"Font file not found: {font_path}")
        return False

    # Copy to Windows fonts directory
    fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
    font_filename = os.path.basename(font_path)
    dest_path = os.path.join(fonts_dir, font_filename)

    try:
        if not os.path.exists(dest_path):
            shutil.copy2(font_path, dest_path)
            print(f"Copied: {font_filename}")
        else:
            print(f"Already exists: {font_filename}")

        # Constants
        FONTS_REG_PATH = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D

        # Setup Windows API calls with proper types
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        gdi32.AddFontResourceW.argtypes = [wintypes.LPCWSTR]
        gdi32.AddFontResourceW.restype = ctypes.c_int

        # Register with Windows API
        result = gdi32.AddFontResourceW(dest_path)

        if result > 0:
            # Determine font type and create proper registry entry
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

            # Add to registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, FONTS_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, registry_name, 0, winreg.REG_SZ, font_filename)
                print(f"Registered: {registry_name}")
            except Exception as reg_error:
                print(f"Registry error for {font_filename}: {reg_error}")

            # Notify system with timeout to prevent hanging
            try:
                user32.SendMessageTimeoutW.argtypes = [
                    wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                    wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                    ctypes.POINTER(wintypes.DWORD)
                ]

                timeout_result = wintypes.DWORD()
                user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_FONTCHANGE, 0, 0,
                    0, 1000, ctypes.byref(timeout_result)  # 1 second timeout
                )
                print(f"System notification sent")
            except Exception:
                # Fallback to simple SendMessage
                user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

            return True
        else:
            print(f"Failed to register: {font_filename}")
            return False

    except Exception as e:
        print(f"Error installing {font_filename}: {e}")
        return False

def main():
    if not is_admin():
        print("ERROR: This script needs to run as Administrator!")
        print("Right-click and 'Run as Administrator'")
        input("Press Enter to exit...")
        return

    downloads_dir = os.path.join(os.getcwd(), "downloaded_fonts")

    if not os.path.exists(downloads_dir):
        print(f"No downloaded_fonts folder found in {os.getcwd()}")
        input("Press Enter to exit...")
        return

    font_files = []
    for file in os.listdir(downloads_dir):
        if file.lower().endswith(('.ttf', '.otf')):
            font_files.append(os.path.join(downloads_dir, file))

    if not font_files:
        print("No font files found in downloaded_fonts folder")
        input("Press Enter to exit...")
        return

    print(f"Found {len(font_files)} font files to install:")
    for font_file in font_files:
        print(f"  {os.path.basename(font_file)}")

    print("\nInstalling fonts...")
    success_count = 0

    for font_file in font_files:
        if install_font(font_file):
            success_count += 1

    print(f"\nCompleted: {success_count}/{len(font_files)} fonts installed successfully")
    print("You may need to restart applications to see the new fonts.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
