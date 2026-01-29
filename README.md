# Term-Radio

A minimal vibecoded terminal-based internet radio player with a ad free retro aesthetic.

```
 ████████╗ ███████╗ ██████╗  ███╗   ███╗
 ╚══██╔══╝ ██╔════╝ ██╔══██╗ ████╗ ████║
    ██║    █████╗   ██████╔╝ ██╔████╔██║
    ██║    ██╔══╝   ██╔══██╗ ██║╚██╔╝██║
    ██║    ███████╗ ██║  ██║ ██║ ╚═╝ ██║
    ╚═╝    ╚══════╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝
 ██████╗   █████╗  ██████╗  ██╗  ██████╗
 ██╔══██╗ ██╔══██╗ ██╔══██╗ ██║ ██╔═══██╗
 ██████╔╝ ███████║ ██║  ██║ ██║ ██║   ██║
 ██╔══██╗ ██╔══██║ ██║  ██║ ██║ ██║   ██║
 ██║  ██║ ██║  ██║ ██████╔╝ ██║ ╚██████╔╝
 ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═════╝  ╚═╝  ╚═════╝
```

## Features

- Clean terminal UI with keyboard controls
- Multiple radio stations (Finnish stations included by default)
- Now playing metadata display
- Volume control
- Easy to add custom stations

## Requirements

- Python 3.10+
- VLC media player

## Installation

### 1. Install VLC

**macOS:**
```bash
brew install --cask vlc
```

**Ubuntu/Debian:**
```bash
sudo apt install vlc
```

### 2. Clone and install

```bash
git clone https://github.com/yourusername/terminal-radio.git
cd terminal-radio
./install.sh
```

### 3. Run

```bash
radio
```

Or run directly:
```bash
python radio.py
```

## Controls

| Key | Action |
|-----|--------|
| `w` / `s` | Navigate up/down |
| `Enter` | Play selected channel |
| `Space` | Pause/Resume |
| `a` / `d` | Volume down/up |
| `1-9` | Quick select channel |
| `m` | Mute toggle |
| `q` | Quit |

## Uninstall

```bash
./uninstall.sh
```

## Adding Channels

Edit `channels.json` to add your own stations:

```json
{
  "channels": [
    {
      "name": "Station Name",
      "url": "https://stream-url.com/stream.mp3",
      "status_url": null
    }
  ]
}
```

- `name`: Display name
- `url`: Stream URL (mp3, aac, m3u8)
- `status_url`: Optional Icecast status JSON URL for listener count

## License

MIT
