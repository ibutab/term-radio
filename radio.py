#!/usr/bin/env python3
import json
import sys
import threading
import time
from pathlib import Path

import requests
import vlc
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ACCENT = "orange1"
DIM = "dim"
MAX_VISIBLE_CHANNELS = 8

console = Console()


class Channel:
    def __init__(self, name: str, url: str, status_url: str | None = None):
        self.name = name
        self.url = url
        self.status_url = status_url


class ChannelManager:
    def __init__(self, config_path: Path):
        self.channels: list[Channel] = []
        self.load(config_path)

    def load(self, path: Path):
        if not path.exists():
            return
        with open(path) as f:
            data = json.load(f)
        for ch in data.get("channels", []):
            self.channels.append(Channel(
                name=ch["name"],
                url=ch["url"],
                status_url=ch.get("status_url")
            ))


class RadioPlayer:
    def __init__(self):
        self.instance = vlc.Instance("--intf", "dummy", "--quiet")
        self.player = self.instance.media_player_new()
        self.volume = 80
        self.player.audio_set_volume(self.volume)
        self.current_channel: Channel | None = None
        self.is_playing = False

    def play(self, channel: Channel):
        self.player.stop()
        self.current_channel = channel
        media = self.instance.media_new(channel.url)
        self.player.set_media(media)
        self.player.play()
        self.player.audio_set_volume(self.volume)
        self.is_playing = True

    def stop(self):
        self.player.stop()
        self.is_playing = False

    def toggle_pause(self):
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        else:
            self.player.play()
            self.is_playing = True

    def set_volume(self, vol: int):
        self.volume = max(0, min(100, vol))
        self.player.audio_set_volume(self.volume)


class MetadataFetcher:
    def __init__(self):
        self.now_playing = ""
        self.listeners = 0
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self, channel: Channel):
        self.running = True
        self.now_playing = ""
        self.listeners = 0
        self.thread = threading.Thread(target=self._fetch_loop, args=(channel,), daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _fetch_loop(self, channel: Channel):
        while self.running:
            self._fetch_metadata(channel)
            time.sleep(10)

    def _fetch_metadata(self, channel: Channel):
        if not channel.status_url:
            self._fetch_icy_metadata(channel)
            return
        try:
            resp = requests.get(channel.status_url, timeout=5)
            data = resp.json()
            if "icestats" in data:
                self._parse_icecast(data, channel)
            elif "songs" in data:
                self._parse_somafm(data)
        except Exception:
            pass

    def _parse_icecast(self, data: dict, channel: Channel):
        sources = data.get("icestats", {}).get("source", [])
        if isinstance(sources, dict):
            sources = [sources]
        for src in sources:
            if channel.url.endswith(src.get("listenurl", "").split("/")[-1]):
                self.listeners = src.get("listeners", 0)
                title = src.get("title") or src.get("yp_currently_playing") or ""
                if title:
                    self.now_playing = title
                break
            if src.get("listenurl") and channel.url in src.get("listenurl", ""):
                self.listeners = src.get("listeners", 0)
                break

    def _parse_somafm(self, data: dict):
        songs = data.get("songs", [])
        if songs:
            song = songs[0]
            artist = song.get("artist", "")
            title = song.get("title", "")
            if artist and title:
                self.now_playing = f"{artist} - {title}"

    def _fetch_icy_metadata(self, channel: Channel):
        try:
            headers = {"Icy-MetaData": "1"}
            resp = requests.get(channel.url, headers=headers, stream=True, timeout=5)
            metaint = resp.headers.get("icy-metaint")
            if metaint:
                metaint = int(metaint)
                data = resp.raw.read(metaint + 4096)
                resp.close()
                self._parse_icy_data(data, metaint)
        except Exception:
            pass

    def _parse_icy_data(self, data: bytes, metaint: int):
        try:
            meta_start = metaint
            length = data[meta_start] * 16
            if length > 0:
                meta = data[meta_start + 1:meta_start + 1 + length].decode("utf-8", errors="ignore")
                if "StreamTitle=" in meta:
                    start = meta.find("StreamTitle='") + 13
                    end = meta.find("';", start)
                    if start > 12 and end > start:
                        self.now_playing = meta[start:end]
        except Exception:
            pass


class TerminalRadio:
    def __init__(self):
        config_path = Path(__file__).parent / "channels.json"
        self.channel_manager = ChannelManager(config_path)
        self.player = RadioPlayer()
        self.metadata = MetadataFetcher()
        self.current_index = 0
        self.running = True

    def get_logo(self) -> str:
        return """ ████████╗ ███████╗ ██████╗  ███╗   ███╗
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
 ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═════╝  ╚═╝  ╚═════╝"""

    def build_display(self) -> Panel:
        total = len(self.channel_manager.channels)
        visible = min(MAX_VISIBLE_CHANNELS, total)
        
        half = visible // 2
        start = max(0, min(self.current_index - half, total - visible))
        end = start + visible

        layout = Layout()
        layout.split_column(
            Layout(name="logo", size=14),
            Layout(name="channels", size=visible + 2),
            Layout(name="now_playing", size=4),
            Layout(name="controls", size=3),
        )

        logo_text = Text(self.get_logo(), style=ACCENT, justify="center")
        layout["logo"].update(logo_text)

        channel_table = Table(show_header=False, box=None, padding=(0, 2))
        channel_table.add_column("marker", width=3)
        channel_table.add_column("num", width=4)
        channel_table.add_column("name")

        if start > 0:
            channel_table.add_row(Text(" ", style=DIM), Text("", style=DIM), Text("↑ more above", style=DIM))

        for i in range(start, end):
            ch = self.channel_manager.channels[i]
            marker = "▶" if i == self.current_index else " "
            marker_style = ACCENT if i == self.current_index else DIM
            name_style = "bold " + ACCENT if i == self.current_index else ""
            num_str = f"{i + 1:2}."
            channel_table.add_row(
                Text(marker, style=marker_style),
                Text(num_str, style=DIM),
                Text(ch.name, style=name_style)
            )

        if end < total:
            channel_table.add_row(Text(" ", style=DIM), Text("", style=DIM), Text("↓ more below", style=DIM))

        channel_title = f"[bold]CHANNELS[/bold] [{self.current_index + 1}/{total}]"
        layout["channels"].update(Panel(
            channel_table,
            title=channel_title,
            title_align="left",
            border_style=DIM
        ))

        now_playing = self.metadata.now_playing or "..."
        listeners = self.metadata.listeners
        channel_name = self.channel_manager.channels[self.current_index].name if self.channel_manager.channels else ""
        status_icon = "▶" if self.player.is_playing else "⏸"
        vol_bar = "█" * (self.player.volume // 10) + "░" * (10 - self.player.volume // 10)
        
        np_text = Text()
        np_text.append(f" {status_icon} ", style=ACCENT if self.player.is_playing else DIM)
        np_text.append(f"{channel_name}", style=f"bold {ACCENT}")
        if listeners > 0:
            np_text.append(f" ({listeners})", style=DIM)
        np_text.append(f"  {vol_bar} {self.player.volume}%\n", style=DIM)
        np_text.append(f"   {now_playing}", style="")

        layout["now_playing"].update(Panel(
            np_text,
            title="[bold]NOW PLAYING[/bold]",
            title_align="left",
            border_style=DIM
        ))

        controls = Text()
        controls.append("  [w/s]", style=ACCENT)
        controls.append(" Nav  ", style=DIM)
        controls.append("[Enter]", style=ACCENT)
        controls.append(" Play  ", style=DIM)
        controls.append("[Space]", style=ACCENT)
        controls.append(" Pause  ", style=DIM)
        controls.append("[a/d]", style=ACCENT)
        controls.append(" Vol  ", style=DIM)
        controls.append("[q]", style=ACCENT)
        controls.append(" Quit", style=DIM)

        layout["controls"].update(Panel(controls, border_style=DIM))

        return layout

    def select_channel(self, index: int):
        if 0 <= index < len(self.channel_manager.channels):
            self.current_index = index
            self.metadata.stop()
            channel = self.channel_manager.channels[index]
            self.player.play(channel)
            self.metadata.start(channel)

    def next_channel(self):
        new_index = (self.current_index + 1) % len(self.channel_manager.channels)
        self.select_channel(new_index)

    def prev_channel(self):
        new_index = (self.current_index - 1) % len(self.channel_manager.channels)
        self.select_channel(new_index)

    def move_selection(self, delta: int):
        total = len(self.channel_manager.channels)
        self.current_index = (self.current_index + delta) % total

    def handle_key(self, key: str):
        if key == "q":
            self.running = False
        elif key == " ":
            self.player.toggle_pause()
        elif key in ("s", "j"):
            self.move_selection(1)
        elif key in ("w", "k"):
            self.move_selection(-1)
        elif key == "n":
            self.next_channel()
        elif key == "p":
            self.prev_channel()
        elif key in ("\r", "\n"):
            self.select_channel(self.current_index)
        elif key in "123456789":
            idx = int(key) - 1
            if idx < len(self.channel_manager.channels):
                self.select_channel(idx)
        elif key in ("+", "=", "d"):
            self.player.set_volume(self.player.volume + 5)
        elif key in ("-", "_", "a"):
            self.player.set_volume(self.player.volume - 5)
        elif key == "m":
            if self.player.volume > 0:
                self._muted_volume = self.player.volume
                self.player.set_volume(0)
            else:
                self.player.set_volume(getattr(self, "_muted_volume", 80))

    def run(self):
        if not self.channel_manager.channels:
            console.print("[red]No channels found in channels.json[/red]")
            return

        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setcbreak(fd)
            
            with Live(self.build_display(), refresh_per_second=4, console=console, screen=True) as live:
                self.select_channel(0)
                
                while self.running:
                    live.update(self.build_display())
                    
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        ch = sys.stdin.read(1)
                        if ch == "\x1b":
                            if select.select([sys.stdin], [], [], 0.05)[0]:
                                ch += sys.stdin.read(2)
                            if ch == "\x1b[A":
                                self.handle_key("w")
                            elif ch == "\x1b[B":
                                self.handle_key("s")
                            elif ch == "\x1b[C":
                                self.handle_key("d")
                            elif ch == "\x1b[D":
                                self.handle_key("a")
                        else:
                            self.handle_key(ch)
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.metadata.stop()
            self.player.stop()
            console.print(f"\n[{ACCENT}]Thanks for listening![/{ACCENT}]")


def main():
    console.clear()
    app = TerminalRadio()
    app.run()


if __name__ == "__main__":
    main()
