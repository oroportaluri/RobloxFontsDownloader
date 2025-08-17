# Roblox Fonts Downloader

Lets you click on funny .exe someone put on the internet and download all the fonts that are in Roblox Studio by default instead of hunting them down for 5 hours.

## Usage

### Quick install

1. Download `RobloxFontsDownloader.exe`
2. Run it (Prompts for admin perms, you're installing fonts)
3. Click "Download Fonts"
4. Worry about wether this is a virus
5. Check the code and find out "Oh nevermind this is just vibe coded garbage"
6. Done

### Development

```bash
pip install -r requirements.txt
python main.py
```

Build executable:

```bash
pyinstaller --onefile --windowed --add-data "config.json;." --name "RobloxFontsDownloader" main.py
```

## How it works

- **CSS parsing**: Extracts font URLs from Google Fonts and Bunny Fonts CSS
- **Direct downloads**: Falls back to ZIP downloads from font repositories
- **Multi-source**: Automatic fallbacks when primary sources fail
- **Smart installation**: Downloads to temp folder, copies to Windows fonts, registers with system
  ^ I didn't write any of this, it was the AI, so yeah it probably does this I have no clue

## Requirements

- Windows 10/11
- Admin privileges (for font installation)
- Internet connection, double check that you have this one by staring at this text and wondering how it got here
- ~50MB disk space, could always uninstall Roblox Studio if you don't have this space

## Configuration

Fonts defined in `config.json` with fallback URLs:

```json
{
  "fonts": {
    "Roboto": {
      "display_name": "Roboto",
      "urls": [
        "https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;900",
        "https://fonts.bunny.net/css?family=Roboto:100,300,400,500,700,900"
      ]
    }
  }
}
```
