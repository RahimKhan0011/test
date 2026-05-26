from __future__ import annotations

import html
import json
import re
import threading
from pathlib import Path

import requests

import main as common

DEFAULT_RELEASE_GROUP = "Dodi"
CUSTOM_TOP_MESSAGE = ""
CUSTOM_BOTTOM_MESSAGE = ""
SKIP_TXT = True
START_HTTP_SERVER = True
HTTP_PORT = common.HTTP_PORT
GAME_CATEGORY = "0"

DEFAULT_IMAGES = {
    "steam": "https://i.postimg.cc/PJjDh09w/steam.png",
    "gog": "https://i.postimg.cc/cJzMq9dR/gog.png",
    "description": "https://i.postimg.cc/g2NHsc5B/description.png",
    "requirements": "https://i.postimg.cc/3wkmZX2d/pcrequirements.png",
    "installNotes": "https://i.postimg.cc/rF91yF8F/installnotes.png",
    "screenshots": "https://i.postimg.cc/mDM9vTX4/screenshots.png",
    "trailer": "https://i.postimg.cc/Y0zWSbBy/trailer.png",
    "checkedIcon": "https://s20.postimg.cc/oinxwrwul/checked.png",
    "uncheckedIcon": "https://s20.postimg.cc/9mpep6dq5/unchecked.png",
}

RELEASE_GROUPS: dict[str, dict[str, object]] = {
    "Dodi": {"type": "repack", "instructions": [
        "Run the installer as administrator",
        "Click on the page",
        "Press the up arrow on your keyboard",
        "Click Install",
        "Click Continue",
        "Select installation destination",
        "Click Next",
        "Select component",
        "Install",
        "Play and enjoy!",
    ]},
    "Fitgirl": {"type": "repack", "instructions": [
        "Run Verify BIN files before installation (Optional)",
        "Run setup.exe",
        "Follow the on-screen instructions and install the game",
        "Play and enjoy!",
    ]},
    "Elamigos": {"type": "repack", "instructions": [
        "Burn or Mount the .iso",
        "Run setup.exe",
        "Follow the on-screen instructions and Install the game",
        "Play and enjoy!",
    ]},
    "Kaos": {"type": "repack", "instructions": [
        "Run Install.exe",
        "Follow the on-screen instructions and install the game",
        "Play and enjoy!",
    ]},
    "RUNE": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack from RUNE folder to installdir",
        "Play and enjoy!",
    ]},
    "FLT": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack from FLT folder to installdir",
        "Play and enjoy!",
    ]},
    "TENOKE": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack to installdir",
        "Play and enjoy!",
    ]},
    "SKIDROW": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack from SKIDROW folder to installdir",
        "Play and enjoy!",
    ]},
    "TiNYiSO": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack from TiNYiSO folder to installdir",
        "Play and enjoy!",
    ]},
    "VOICES38": {"type": "scene", "instructions": [
        "Burn or mount the .iso",
        "Run setup.exe and install",
        "Copy crack to installdir",
        "Play and enjoy!",
    ]},
    "GOG": {"type": "scene", "instructions": [
        "Run the installer as administrator",
        "Follow the on-screen instructions and install the game",
        "Install DLCs using the provided exe's if there are any",
        "Play and enjoy!",
    ]},
    "SteamBackup": {"type": "backup", "instructions": [
        "Launch Steam",
        "On the Upper Left Corner click on 'Steam' and Select 'Restore Game Backup' from the drop-down menu",
        "Then browse to the directory of the backup (select the folder that you downloaded)",
        "Click 'Next' and it'll start restoring the backup",
        "As soon as the restoring process is finished, you are Ready to Play!",
    ]},
    "EpicBackup": {"type": "backup", "instructions": [
        "Run 'Epic Games Launcher'",
        "Right-click on the game you want to install, click Install, and choose the directory where you want to install the game",
        "Once the Epic Launcher starts to download, let it download 4-5 MiB, then pause the download and exit Epic Games Launcher (better to close it from Task Manager)",
        "Go to the installation path you chose earlier and delete the newly created folder for the game",
        "Copy the game folder you downloaded and Paste it into the Epic Games directory (the location of the folder you just deleted)",
        "Again, open Epic Games Launcher and click Resume",
        "It will detect and verify the files",
    ]},
    "RockstarBackup": {"type": "backup", "instructions": [
        "Open Rockstar Games Launcher and Sign In to your account",
        "Select 'Install Now' (in the game)",
        "Select the location where you've downloaded the game",
        "Then wait for the launcher to verify the files, and after that you're good to go",
        "[color=#3CB371][b]OR[/b][/color]",
        "Open Rockstar Games Launcher and Sign In to your account",
        "Go to Settings > General and hit 'Scan Now'",
        "It'll begin locating your game from the directory you've downloaded to",
    ]},
    "EABackup": {"type": "backup", "instructions": [
        "[color=#3CB371][b]METHOD 1: ORIGIN APP[/b][/color]",
        "Right-click on the game you want to install from the Origin Library and click Locate Game",
        "Then choose the folder that you've just downloaded",
        "Origin will begin locating and installing the game right away",
        "[color=#3CB371][b]METHOD 2: EA APP[/b][/color]",
        "Select the game you want to install",
        "Choose the download folder as the directory for the game in the EA Desktop App",
        "The game will automatically load in the EA Desktop App",
    ]},
    "UbisoftBackup": {"type": "backup", "instructions": [
        "Open Ubisoft Connect on your PC (you have to install it from the Ubisoft website if you don't have it installed on your PC)",
        "Search for the game in the Games section",
        "Tap Locate Installed Game and open the folder of your downloaded directory",
        "The software will detect the files and verify them",
        "After completion, play the game directly from Ubisoft software",
    ]},
    "BattleNetBackup": {"type": "backup", "instructions": [
        "Go to your Battle.net App, open the game, and click Locate The Game",
        "Select the directory where the downloaded files are stored",
        "The app will start discovering the existing files and begin the installation",
        "",
        "If You Encounter the Error: 'This Folder Doesn't Contain The Correct Version Of This Game':",
        "Click on the Blizzard logo in the top left corner of the Blizzard app",
        "Select Settings",
        "Go to Downloads",
        "Click on Scan for Games and allow the app to search for Blizzard games on your computer",
        "Once located, click on Update",
    ]},
    "RiotBackup": {"type": "backup", "instructions": [
        "Copy the downloaded Riot Games folder and place it in whichever directory you wish to (C Drive recommended)",
        "Install the Riot Games launcher from the official website",
        'Launch the .exe file, go to Advanced Settings and write the path to the Folder "Riot Games" (which you have already copied to local drive)',
        "The client will automatically search for the predownloaded game files",
        "You can play it now",
    ]},
    "RUNE-Update": {"type": "update", "instructions": [
        "Go to Update folder",
        "Run setup.exe",
        "Follow the on-screen instructions and wait for patching to be finished",
        "Copy crack from RUNE folder to installdir",
        "Play and enjoy!",
    ]},
    "TENOKE-Update": {"type": "update", "instructions": [
        "Go to Update folder",
        "Run Patch.exe",
        "Follow the on-screen instructions and wait for patching to be finished",
        "Copy crack to installdir",
        "Play and enjoy!",
    ]},
    "Elamigos-Update": {"type": "update", "instructions": [
        "Run the provided exe",
        "Follow the on-screen instructions and wait for patching to be finished",
        "Play and enjoy!",
    ]},
}

RELEASE_GROUP_KEYWORDS = {
    "Dodi": ["DODI", "dodi", "[dodi]", "(dodi)", "(DODI REPACK)", "[DODI REPACK]", "[DODI-REPACK]", "(DODI-REPACK)", "{DODI}", "{DODI REPACK}", "{DODI-Repack}", "DODIRepack"],
    "Fitgirl": ["FitGirl", "Fitgirl", "fitgirl", "[FitGirl]", "(FitGirl)", "{FitGirl}", "FitGirlrepack"],
    "Kaos": ["KaOs", "kaos", "(kaos)", "[kaos]", "[kaos repack]", "[kaos-repack]", "(kaos repack)", "(kaos-repack)", "{kaos-repack}", "{kaos repack}", "kaosrepack"],
    "Elamigos": ["ElAmigos", "[ElAmigos]", "(ElAmigos)", "(ElAmigos REPACK)", "[ElAmigos REPACK]", "[ElAmigos-REPACK]", "(ElAmigos-REPACK)", "{ElAmigos}", "{ElAmigos REPACK}", "{ElAmigos-Repack}", "ElAmigosRepack"],
    "RUNE": ["RUNE", "-RUNE", "(RUNE)", "[RUNE]"],
    "FLT": ["FLT", "-FLT", "(FLT)", "[FLT]", "FAIRLIGHT"],
    "TENOKE": ["TENOKE", "-TENOKE", "(TENOKE)", "[TENOKE]"],
    "SKIDROW": ["SKIDROW", "-SKIDROW", "(SKIDROW)", "[SKIDROW]"],
    "TiNYiSO": ["TiNYiSO", "-TiNYiSO", "(TiNYiSO)", "[TiNYiSO]", "TINYISO"],
    "VOICES38": ["VOICES38", "-VOICES38", "(VOICES38)", "[VOICES38]"],
    "GOG": ["GOG", "-GOG", "(GOG)", "[GOG]", "GOG.COM"],
    "SteamBackup": ["[Steam Game Launcher Backup]", "Steam Game Backup", "[Steam Game Backup]", "Steam-Backup", "Steam Backup", "[Steam Backup]", "(Steam Backup)", "{Steam Backup}", "{Steam-Backup}", "[Steam-Backup]", "(Steam-Backup)"],
    "EpicBackup": ["Epic Games Launcher Backup", "[Epic Games Launcher Backup]", "[Epic Games Store Backup]", "Epic Games Store Backup", "Epic-Games-Store-Backup", "Epic Backup", "Epic Game Backup", "[Epic Game Backup]", "Epic-Backup", "[Epic-Backup]", "(Epic Backup)", "[Epic Backup]", "{Epic Backup}", "Epic Games Backup", "(Epic Games Backup)", "[Epic Games Backup]", "{Epic Games Backup}"],
    "RockstarBackup": ["[Rockstar Games Launcher Backup]", "[Rockstar Games Backup]", "Rockstar Games Backup", "Rockstar Backup", "(Rockstar Backup)", "[Rockstar Backup]", "{Rockstar Backup}", "Rockstar Launcher Backup", "(Rockstar Launcher Backup)", "[Rockstar Launcher Backup]", "{Rockstar Launcher Backup}"],
    "EABackup": ["[EA Backup]", "EA Backup", "EAOrigin Backup", "[EAOrigin Backup]", "Origin/EA Backup", "[Origin/EA Backup]", "EA-Backup", "(EA Backup)", "{EA Backup}", "EA/Origin Game Launcher Backup", "EA/Origin Game Backup", "EA/Origin Backup", "(EA/Origin Backup)", "[EA/Origin Backup]", "{EA/Origin Backup}", "Origin Backup", "(Origin Backup)", "[Origin Backup]", "{Origin Backup}", "EA APP Backup", "(EA APP Backup)", "[EA APP Backup]", "{EA APP Backup}"],
    "UbisoftBackup": ["Ubisoft Connect Backup", "Ubisoft Backup", "[Ubisoft Connect Files]", "[Ubisoft Connect Backup]", "(Ubisoft Connect Backup)", "[Ubisoft Connect Backup]", "{Ubisoft Connect Backup}", "(Ubisoft Backup)", "[Ubisoft Backup]", "{Ubisoft Backup}"],
    "BattleNetBackup": ["[Battle", "[Battle Blizzard Backup]", "[Battle.net Blizzard Backup]", "[Battle.net Backup]", "Battle net Files", "Battle.net Files", "Battle Files", "[Battle Files]", "Battle net Backup", "(Battle net Backup)", "[Battle net Backup]", "{Battle net Backup}", "Battle.net Backup", "(Battle.net Backup)", "[Battle.net Backup]", "{Battle.net Backup}"],
    "RiotBackup": ["Riot Games Backup", "[Riot Games Backup]", "(Riot Games Backup)", "{Riot Games Backup}", "Riot Backup", "[Riot Backup]", "(Riot Backup)", "{Riot Backup}", "Riot Games Launcher Backup", "[Riot Games Launcher Backup]", "(Riot Games Launcher Backup)", "{Riot Games Launcher Backup}"],
    "RUNE-Update": ["RUNE Update", "[RUNE Update]", "(RUNE Update)", "{RUNE Update}", "RUNE-Update", "[RUNE-Update]", "(RUNE-Update)", "RUNE.Update", "Update-RUNE", "[Update RUNE]"],
    "TENOKE-Update": ["TENOKE Update", "[TENOKE Update]", "(TENOKE Update)", "{TENOKE Update}", "TENOKE-Update", "[TENOKE-Update]", "(TENOKE-Update)", "TENOKE.Update", "Update-TENOKE", "[Update TENOKE]"],
    "Elamigos-Update": ["ElAmigos Update", "[ElAmigos Update]", "(ElAmigos Update)", "{ElAmigos Update}", "ElAmigos-Update", "[ElAmigos-Update]", "(ElAmigos-Update)", "ElAmigos.Update", "Update-ElAmigos", "[Update ElAmigos]", "Elamigos Update", "Elamigos-Update"],
}

PROTECTION_MAP = {
    "GOG": "NO PROTECTION",
    "SteamBackup": "STEAM",
    "EpicBackup": "EPIC ONLINE SERVICES",
    "RockstarBackup": "ROCKSTAR SOCIAL CLUB",
    "EABackup": "EA APP",
    "UbisoftBackup": "UBISOFT CONNECT",
    "BattleNetBackup": "BATTLE.NET",
    "RiotBackup": "RIOT CLIENT",
    "RUNE-Update": "STEAM",
    "TENOKE-Update": "STEAM",
    "Elamigos-Update": "STEAM",
}

LANGUAGE_IDS = {
    "english": "1",
    "french": "2",
    "hindi": "3",
    "urdu": "4",
    "chinese": "5",
    "spanish": "6",
    "japanese": "7",
    "bengali": "8",
    "german": "9",
    "korean": "10",
    "telugu": "11",
    "italian": "12",
    "russian": "13",
    "bulgarian": "14",
    "czech": "15",
    "filipino": "16",
    "hungarian": "17",
    "arabic": "18",
    "serbian": "19",
    "swedish": "20",
    "tamil": "21",
    "turkish": "22",
    "vietnamese": "23",
    "danish": "24",
    "dutch": "25",
    "finnish": "26",
    "greek": "27",
    "hebrew": "28",
    "icelandic": "30",
    "indonesian": "31",
    "irish": "32",
    "malayalam": "33",
    "marathi": "34",
    "norwegian": "35",
    "persian": "36",
    "polish": "37",
    "portuguese": "38",
    "romanian": "39",
    "thai": "40",
    "kannada": "41",
    "panjabi": "43",
}


def normalize_app_id(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        return value
    match = re.search(r"/app/(\d+)", value)
    if match:
        return match.group(1)
    return None


def detect_release_group(name: str) -> str:
    update_match = "update" in name.lower()
    if update_match:
        if re.search(r"\b(RUNE|-RUNE|\[RUNE\]|\(RUNE\))\b", name, re.I):
            return "RUNE-Update"
        if re.search(r"\b(TENOKE|-TENOKE|\[TENOKE\]|\(TENOKE\))\b", name, re.I):
            return "TENOKE-Update"
        if re.search(r"\b(ElAmigos|Elamigos|ELAMIGOS|\[ElAmigos\]|\(ElAmigos\)|-ElAmigos)\b", name, re.I):
            return "Elamigos-Update"

    backup_groups = [key for key in RELEASE_GROUP_KEYWORDS if "Backup" in key]
    for group_name in backup_groups:
        for keyword in RELEASE_GROUP_KEYWORDS[group_name]:
            if re.search(re.escape(keyword), name, re.I):
                return group_name

    for group_name, keywords in RELEASE_GROUP_KEYWORDS.items():
        if "Backup" in group_name or "Update" in group_name:
            continue
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", name, re.I):
                return group_name

    return DEFAULT_RELEASE_GROUP


def prompt_for_app_id(default_hint: str) -> str:
    while True:
        raw = input(f"{common.c.BOLD}Enter Steam app id or URL for {default_hint}: {common.c.RESET}").strip()
        app_id = normalize_app_id(raw)
        if app_id:
            return app_id
        print(f"{common.c.RED}Invalid Steam app id or URL.{common.c.RESET}")


def prompt_for_release_group(default_group: str) -> str:
    groups = list(RELEASE_GROUPS.keys())
    print(f"{common.c.CYAN}Detected release group: {default_group}{common.c.RESET}")
    print(f"{common.c.DIM}Available groups: {', '.join(groups)}{common.c.RESET}")
    while True:
        raw = input(f"{common.c.BOLD}Release group [{default_group}]: {common.c.RESET}").strip()
        selected = raw or default_group
        if selected in RELEASE_GROUPS:
            return selected
        print(f"{common.c.RED}Unknown release group.{common.c.RESET}")


def clean_html_text(value: str) -> str:
    text = value or ""
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</li>\s*", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "", text, flags=re.I)
    text = re.sub(r"</?(?:ul|ol|p|div)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</?strong[^>]*>", "", text, flags=re.I)
    text = re.sub(r"</?h\d[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_supported_languages(value: str) -> list[str]:
    primary_block = (value or "").split("<br>")[0]
    cleaned = clean_html_text(primary_block)
    return [part.replace("*", "").strip() for part in cleaned.split(",") if part.strip()]


def format_system_requirements(pc_requirements: dict) -> str:
    if not pc_requirements or not pc_requirements.get("minimum"):
        return "No system requirements available."
    combined_html = f"{pc_requirements.get('minimum', '')}{pc_requirements.get('recommended', '')}"
    sys_req = clean_html_text(combined_html)
    replacements = (
        (r"Minimum:", "[b]Minimum:[/b]"),
        (r"Recommended:", "\n\n[b]Recommended:[/b]"),
        (r"Requires a 64-bit processor and operating system", ""),
        (r"OS\s*\*?:", "\n➩ [b]OS:[/b]"),
        (r"Processor:", "\n➩ [b]Processor:[/b]"),
        (r"Memory:", "\n➩ [b]Memory:[/b]"),
        (r"Graphics:", "\n➩ [b]Graphics:[/b]"),
        (r"DirectX®?:", "\n➩ [b]DirectX:[/b]"),
        (r"Storage:", "\n➩ [b]Storage:[/b]"),
        (r"Hard Drive:", "\n➩ [b]Storage:[/b]"),
        (r"Sound Card:", "\n➩ [b]Sound Card:[/b]"),
        (r"Sound:", "\n➩ [b]Sound Card:[/b]"),
        (r"Network:", "\n➩ [b]Network:[/b]"),
        (r"VR Support:", "\n➩ [b]VR Support:[/b]"),
        (r"VR:", "\n➩ [b]VR Support:[/b]"),
        (r"Other Requirements:", "\n➩ [b]Other Requirements:[/b]"),
        (r"Additional Notes:", "\n➩ [b]Additional Notes:[/b]"),
        (r"Additional:", "\n➩ [b]Additional:[/b]"),
    )
    for pattern, replacement in replacements:
        sys_req = re.sub(pattern, replacement, sys_req, flags=re.I)
    sys_req = re.sub(r"\n\s*\n", "\n", sys_req).strip()
    parts = sys_req.split("[b]Recommended:[/b]")
    if len(parts) == 2 and not parts[1].strip():
        sys_req = parts[0].strip()
    return sys_req or "No system requirements available."


def build_trailer_url(data: dict) -> str:
    movies = data.get("movies") or []
    for movie in movies:
        if not isinstance(movie, dict):
            continue
        mp4 = (movie.get("mp4") or {}).get("max")
        webm = (movie.get("webm") or {}).get("max")
        if mp4:
            return mp4
        if webm:
            return webm
    return ""


def fetch_steam_game_info(app_id: str, release_group: str) -> dict:
    response = requests.get(
        f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=en",
        timeout=20,
    )
    response.raise_for_status()
    api_data = response.json()
    app_data = api_data.get(app_id) or {}
    if not app_data.get("success"):
        raise RuntimeError("Steam API returned no data for this app id.")
    data = app_data.get("data") or {}

    info = {
        "appId": app_id,
        "title": data.get("name") or "",
        "headerImage": (data.get("header_image") or f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg").split("?")[0],
        "type": (data.get("type") or "game").capitalize(),
        "genres": [
            {
                "text": genre.get("description", ""),
                "url": f"https://store.steampowered.com/genre/{requests.utils.quote(genre.get('description', ''))}/",
            }
            for genre in (data.get("genres") or [])
            if genre.get("description")
        ],
        "publishers": [
            {
                "text": publisher,
                "url": f"https://store.steampowered.com/search/?publisher={requests.utils.quote(publisher)}",
            }
            for publisher in (data.get("publishers") or [])
            if publisher
        ],
        "website": data.get("website") or "",
        "releaseDate": ((data.get("release_date") or {}).get("date")) or "",
        "price": ((data.get("price_overview") or {}).get("final_formatted")) or ("Free" if data.get("is_free") else "No price found"),
        "url": f"https://store.steampowered.com/app/{app_id}",
        "platforms": {
            "windows": ((data.get("platforms") or {}).get("windows")) or False,
            "mac": ((data.get("platforms") or {}).get("mac")) or False,
            "linux": ((data.get("platforms") or {}).get("linux")) or False,
        },
        "languages": parse_supported_languages(data.get("supported_languages") or ""),
        "protection": PROTECTION_MAP.get(release_group, "STEAM"),
        "description": data.get("short_description") or "",
        "systemRequirements": format_system_requirements(data.get("pc_requirements") or {}),
        "screenshots": [
            ((shot.get("path_full") or "").replace("https://cdn.akamai.steamstatic.com", "https://shared.akamai.steamstatic.com").replace("https://cdn.cloudflare.steamstatic.com", "https://shared.akamai.steamstatic.com").split("?")[0])
            for shot in (data.get("screenshots") or [])
            if shot.get("path_full")
        ],
        "trailer": build_trailer_url(data),
    }
    if data.get("drm_notice") and re.search(r"denuvo", data["drm_notice"], re.I) and release_group not in PROTECTION_MAP:
        info["protection"] = "DENUVO & STEAM"
    return info


def choose_language_id(languages: list[str]) -> str:
    if not languages:
        return "0"
    lowered = {language.lower(): language for language in languages}
    if "english" in lowered:
        return "1"
    for language in languages:
        language_id = LANGUAGE_IDS.get(language.lower())
        if language_id:
            return language_id
    return "0"


def get_image_url(kind: str, is_gog: bool = False) -> str:
    if kind == "info":
        return DEFAULT_IMAGES["gog"] if is_gog else DEFAULT_IMAGES["steam"]
    return DEFAULT_IMAGES[kind]


def generate_complete_description(info: dict, release_group_name: str) -> str:
    is_gog = release_group_name == "GOG"
    release_group = RELEASE_GROUPS.get(release_group_name, {})
    is_backup = release_group.get("type") == "backup"
    instructions = release_group.get("instructions") or []

    lines: list[str] = []
    if CUSTOM_TOP_MESSAGE.strip():
        lines.extend([CUSTOM_TOP_MESSAGE.strip(), ""])

    lines.append("[font=Consolas]")
    lines.append(f"[center][img]{info['headerImage']}[/img][/center]")
    if info["title"]:
        lines.extend(["", f"[center][size=5][color=orange]{info['title']}[/color][/size][/center]"])

    lines.extend(["", f"[img]{get_image_url('info', is_gog)}[/img]", ""])
    lines.append(f"[color=magenta]Type:...............[/color] {info['type']}")
    if info["genres"]:
        genre_text = ", ".join(f"[url={genre['url']}]{genre['text']}[/url]" for genre in info["genres"])
        lines.append(f"[color=magenta]Genre:..............[/color] {genre_text}")
    if info["publishers"]:
        publisher_text = ", ".join(f"[url={publisher['url']}]{publisher['text']}[/url]" for publisher in info["publishers"])
        lines.append(f"[color=magenta]Publisher:..........[/color] {publisher_text}")
    if info["website"]:
        lines.append(f"[color=magenta]Website:............[/color] {info['website']}")
    if info["releaseDate"]:
        lines.append(f"[color=magenta]Release date:.......[/color] {info['releaseDate']}")
    lines.append(f"[color=magenta]Price:..............[/color] {info['price']}")
    lines.append(f"[color=magenta]Url:................[/color] [url={info['url']}]{info['url']}[/url]")
    windows_icon = f"[img]{DEFAULT_IMAGES['checkedIcon']}[/img]" if info["platforms"]["windows"] else f"[img]{DEFAULT_IMAGES['uncheckedIcon']}[/img]"
    mac_icon = f"[img]{DEFAULT_IMAGES['checkedIcon']}[/img]" if info["platforms"]["mac"] else f"[img]{DEFAULT_IMAGES['uncheckedIcon']}[/img]"
    linux_icon = f"[img]{DEFAULT_IMAGES['checkedIcon']}[/img]" if info["platforms"]["linux"] else f"[img]{DEFAULT_IMAGES['uncheckedIcon']}[/img]"
    lines.append(f"[color=magenta]Platforms:..........[/color] Windows:{windows_icon} MacOSX:{mac_icon} Linux:{linux_icon}")
    if info["languages"]:
        lines.append(f"[color=magenta]Languages:..........[/color] {', '.join(info['languages'])}")
    lines.append(f"[color=magenta]Protection..........[/color] {info['protection']}")

    lines.extend(["", f"[img]{get_image_url('description')}[/img]", ""])
    if info["description"]:
        lines.extend([info["description"], ""])

    lines.extend([f"[img]{get_image_url('requirements')}[/img]", ""])
    if info["systemRequirements"]:
        lines.extend([info["systemRequirements"], ""])

    lines.extend([f"[img]{get_image_url('installNotes')}[/img]", ""])
    if instructions:
        for instruction in instructions:
            if instruction:
                lines.append(f"➩ {instruction}")
            else:
                lines.append("")
        lines.extend(["", "NOTES"])
        if is_backup:
            lines.append("➩ Don't seed and play from the same folder, it will cause network issues and possible FPS issues; and future updates will cause errors in seeding")
        else:
            lines.append("➩ Don't forget to add an exception to your antivirus (if required)")
            lines.append("➩ Block all game executables in your firewall")
        lines.append("")

    lines.extend([f"[img]{get_image_url('screenshots')}[/img]", "", "[center]"])
    for screenshot in info["screenshots"]:
        lines.append(f"[img]{screenshot}[/img]")
    lines.append("[/center]")
    if info["trailer"]:
        lines.extend(["", f"[img]{get_image_url('trailer')}[/img]", "", f"[center]{info['trailer']}", "[/center]", ""])
    lines.append("[/font]")

    if CUSTOM_BOTTOM_MESSAGE.strip():
        lines.extend(["", CUSTOM_BOTTOM_MESSAGE.strip()])
    return "\n".join(lines).strip()


def prepare_sync_files(sync_dir: Path, target_path: Path) -> None:
    common.LATEST_JSON = sync_dir / "latest.json"
    common.INDEX_HTML = sync_dir / "index.html"
    common.COVER_PATH = None
    common.EXTRACTED_COVER = None
    common.GENERATED_TXT = None

    stale_paths = [
        common.LATEST_JSON,
        common.INDEX_HTML,
        sync_dir / f"{target_path.name}.torrent",
    ]
    for stale_path in stale_paths:
        if stale_path.exists():
            try:
                stale_path.unlink()
                common.log(f"Removed stale file: {stale_path.name}", "Cleanup", common.c.YELLOW)
            except OSError:
                pass
    try:
        common.INDEX_HTML.write_text(common._WEBAPP_HTML, encoding="utf-8")
    except OSError as exc:
        common.error(f"Could not write temporary index.html: {exc}")


def write_description_file(target_path: Path, description: str, is_folder: bool) -> None:
    if SKIP_TXT:
        return
    save_name = f"{target_path.name}_description.txt" if is_folder else f"{target_path.stem}_TBD_Description.txt"
    txt_path = target_path.parent / save_name
    txt_path.write_text(description, encoding="utf-8")
    common.GENERATED_TXT = txt_path
    common.success(f"Saved → {save_name}")


def stage_web_payload(title: str, description: str, torrent_filename: str, language: str) -> None:
    payload = {
        "ready": True,
        "title": title,
        "category": GAME_CATEGORY,
        "language": language,
        "description": description,
        "torrentFile": torrent_filename,
    }
    with open(common.LATEST_JSON, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def main() -> None:
    common.clear()
    common.banner()

    target_path, is_folder = common.select_target()
    if not target_path or not target_path.exists():
        return

    sync_dir = target_path.parent
    prepare_sync_files(sync_dir, target_path)

    display_name = target_path.name if is_folder else target_path.stem
    detected_group = detect_release_group(target_path.name)
    app_id = prompt_for_app_id(display_name)
    release_group = prompt_for_release_group(detected_group)

    torrent_result = [False]

    def _torrent_worker() -> None:
        torrent_result[0] = common.create_torrent(target_path)

    torrent_thread = threading.Thread(target=_torrent_worker, daemon=True, name="game-torrent-creator")
    torrent_thread.start()

    common.log("Fetching Steam game info...", "Steam")
    info = fetch_steam_game_info(app_id, release_group)
    description = generate_complete_description(info, release_group)
    common.success("Game description generated!")

    write_description_file(target_path, description, is_folder)
    common.copy_to_clipboard(description)

    if START_HTTP_SERVER:
        try:
            torrent_filename = f"{target_path.name}.torrent"
            stage_web_payload(
                title=target_path.name,
                description=description,
                torrent_filename=torrent_filename,
                language=choose_language_id(info["languages"]),
            )
            common.success("Sync files ready for Localhost!")
            common._server_ready_event.clear()
            common.start_server_thread(HTTP_PORT)
        except Exception as exc:
            common.error(f"HTTP Sync Failed: {exc}")

    torrent_thread.join()
    if START_HTTP_SERVER:
        common._server_ready_event.wait(timeout=5)

    if torrent_result[0] or not common.CREATE_TORRENT_FILE:
        print(f"\n{common.c.BOLD}{common.c.GREEN}ALL DONE!{common.c.RESET}")
    else:
        print(f"\n{common.c.BOLD}{common.c.YELLOW}DONE (torrent creation failed — description still copied to clipboard).{common.c.RESET}")
    print(f"{common.c.DIM}When you exit, sync files & generated torrents will be deleted.{common.c.RESET}")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{common.c.YELLOW}Cancelled.{common.c.RESET}")
    except (requests.RequestException, RuntimeError, json.JSONDecodeError) as exc:
        common.error(str(exc))
