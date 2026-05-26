// ==UserScript==
// @name         Game Description Extractor for TBD
// @namespace    SteamExtractor
// @version      2.0
// @description  Extract full Steam game details into formatted BBCode for TorrentBD - Works on Steam pages and TBD upload page
// @author       notPULS3
// @license      MIT
// @icon         https://img2.ptscreens.com/gamepad.png
// @match        https://store.steampowered.com/app/*
// @match        https://www.torrentbd.net/torrents-upload.php
// @match        https://www.torrentbd.me/torrents-upload.php
// @match        https://www.torrentbd.com/torrents-upload.php
// @grant        GM_xmlhttpRequest
// @run-at       document-end
// @downloadURL https://update.greasyfork.org/scripts/551951/Game%20Description%20Extractor%20for%20TBD.user.js
// @updateURL https://update.greasyfork.org/scripts/551951/Game%20Description%20Extractor%20for%20TBD.meta.js
// ==/UserScript==

(function() {
    'use strict';

    // ============================================
    // USER CONFIGURATION
    // ============================================

    const DEFAULT_RELEASE_GROUP = 'Dodi';
    const CUSTOM_TOP_MESSAGE = '';
    const CUSTOM_BOTTOM_MESSAGE = '';

    const customImages = {
        info: '',
        description: '',
        requirements: '',
        installNotes: '',
        screenshots: '',
        trailer: ''
    };

    // ============================================

    const isTBDUploadPage = window.location.href.includes('torrents-upload.php');
    const isSteamPage = window.location.href.includes('store.steampowered.com');

    var youtubeApiKeys = [
        '',
    ];

    var internalYoutubeApiKeys = [
        'AIzaSyDdf4cS-foL69U7-m2aYhB5gftUC3t01PI',
        'AIzaSyCqZcGyWKFX3li4GRQ4bidrsIzjG52VzTY',
    ];

    var combinedYoutubeApiKeys = youtubeApiKeys.length > 0 ? youtubeApiKeys.concat(internalYoutubeApiKeys) : internalYoutubeApiKeys;

    const defaultImages = {
        steam: 'https://i.postimg.cc/PJjDh09w/steam.png',
        gog: 'https://i.postimg.cc/cJzMq9dR/gog.png',
        description: 'https://i.postimg.cc/g2NHsc5B/description.png',
        requirements: 'https://i.postimg.cc/3wkmZX2d/pcrequirements.png',
        installNotes: 'https://i.postimg.cc/rF91yF8F/installnotes.png',
        screenshots: 'https://i.postimg.cc/mDM9vTX4/screenshots.png',
        trailer: 'https://i.postimg.cc/Y0zWSbBy/trailer.png',
        checkedIcon: 'https://s20.postimg.cc/oinxwrwul/checked.png',
        uncheckedIcon: 'https://s20.postimg.cc/9mpep6dq5/unchecked.png'
    };

    function getImageUrl(type, isGOG = false) {
        if (type === 'info') {
            if (customImages.info) return customImages.info;
            return isGOG ? defaultImages.gog : defaultImages.steam;
        }
        if (customImages[type]) return customImages[type];
        return defaultImages[type];
    }

    const releaseGroups = {
        'Dodi': {
            type: 'repack',
            instructions: [
                'Run the installer as administrator',
                'Click on the page',
                'Press the up arrow on your keyboard',
                'Click Install',
                'Click Continue',
                'Select installation destination',
                'Click Next',
                'Select component',
                'Install',
                'Play and enjoy!'
            ]
        },
        'Fitgirl': {
            type: 'repack',
            instructions: [
                'Run Verify BIN files before installation (Optional)',
                'Run setup.exe',
                'Follow the on-screen instructions and install the game',
                'Play and enjoy!'
            ]
        },
        'Elamigos': {
            type: 'repack',
            instructions: [
                'Burn or Mount the .iso',
                'Run setup.exe',
                'Follow the on-screen instructions and Install the game',
                'Play and enjoy!'
            ]
        },
        'Kaos': {
            type: 'repack',
            instructions: [
                'Run Install.exe',
                'Follow the on-screen instructions and install the game',
                'Play and enjoy!'
            ]
        },
        'RUNE': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack from RUNE folder to installdir',
                'Play and enjoy!'
            ]
        },
        'FLT': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack from FLT folder to installdir',
                'Play and enjoy!'
            ]
        },
        'TENOKE': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack to installdir',
                'Play and enjoy!'
            ]
        },
        'SKIDROW': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack from SKIDROW folder to installdir',
                'Play and enjoy!'
            ]
        },
        'TiNYiSO': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack from TiNYiSO folder to installdir',
                'Play and enjoy!'
            ]
        },
        'VOICES38': {
            type: 'scene',
            instructions: [
                'Burn or mount the .iso',
                'Run setup.exe and install',
                'Copy crack to installdir',
                'Play and enjoy!'
            ]
        },
        'GOG': {
            type: 'scene',
            instructions: [
                'Run the installer as administrator',
                'Follow the on-screen instructions and install the game',
                'Install DLCs using the provided exe\'s if there are any',
                'Play and enjoy!'
            ]
        },
        'SteamBackup': {
            type: 'backup',
            instructions: [
                'Launch Steam',
                'On the Upper Left Corner click on \'Steam\' and Select \'Restore Game Backup\' from the drop-down menu',
                'Then browse to the directory of the backup (select the folder that you downloaded)',
                'Click \'Next\' and it\'ll start restoring the backup',
                'As soon as the restoring process is finished, you are Ready to Play!'
            ]
        },
        'EpicBackup': {
            type: 'backup',
            instructions: [
                'Run \'Epic Games Launcher\'',
                'Right-click on the game you want to install, click Install, and choose the directory where you want to install the game',
                'Once the Epic Launcher starts to download, let it download 4-5 MiB, then pause the download and exit Epic Games Launcher (better to close it from Task Manager)',
                'Go to the installation path you chose earlier and delete the newly created folder for the game',
                'Copy the game folder you downloaded and Paste it into the Epic Games directory (the location of the folder you just deleted)',
                'Again, open Epic Games Launcher and click Resume',
                'It will detect and verify the files'
            ]
        },
        'RockstarBackup': {
            type: 'backup',
            instructions: [
                'Open Rockstar Games Launcher and Sign In to your account',
                'Select \'Install Now\' (in the game)',
                'Select the location where you\'ve downloaded the game',
                'Then wait for the launcher to verify the files, and after that you\'re good to go',
                '[color=#3CB371][b]OR[/b][/color]',
                'Open Rockstar Games Launcher and Sign In to your account',
                'Go to Settings > General and hit \'Scan Now\'',
                'It\'ll begin locating your game from the directory you\'ve downloaded to'
            ]
        },
        'EABackup': {
            type: 'backup',
            instructions: [
                '[color=#3CB371][b]METHOD 1: ORIGIN APP[/b][/color]',
                'Right-click on the game you want to install from the Origin Library and click Locate Game',
                'Then choose the folder that you\'ve just downloaded',
                'Origin will begin locating and installing the game right away',
                '[color=#3CB371][b]METHOD 2: EA APP[/b][/color]',
                'Select the game you want to install',
                'Choose the download folder as the directory for the game in the EA Desktop App',
                'The game will automatically load in the EA Desktop App'
            ]
        },
        'UbisoftBackup': {
            type: 'backup',
            instructions: [
                'Open Ubisoft Connect on your PC (you have to install it from the Ubisoft website if you don\'t have it installed on your PC)',
                'Search for the game in the Games section',
                'Tap Locate Installed Game and open the folder of your downloaded directory',
                'The software will detect the files and verify them',
                'After completion, play the game directly from Ubisoft software'
            ]
        },
        'BattleNetBackup': {
            type: 'backup',
            instructions: [
                'Go to your Battle.net App, open the game, and click Locate The Game',
                'Select the directory where the downloaded files are stored',
                'The app will start discovering the existing files and begin the installation',
                '',
                'If You Encounter the Error: \'This Folder Doesn\'t Contain The Correct Version Of This Game\':',
                'Click on the Blizzard logo in the top left corner of the Blizzard app',
                'Select Settings',
                'Go to Downloads',
                'Click on Scan for Games and allow the app to search for Blizzard games on your computer',
                'Once located, click on Update'
            ]
        },
        'RiotBackup': {
            type: 'backup',
            instructions: [
                'Copy the downloaded Riot Games folder and place it in whichever directory you wish to (C Drive recommended)',
                'Install the Riot Games launcher from the official website',
                'Launch the .exe file, go to Advanced Settings and write the path to the Folder "Riot Games" (which you have already copied to local drive)',
                'The client will automatically search for the predownloaded game files',
                'You can play it now'
            ]
        },
        'RUNE-Update': {
            type: 'update',
            instructions: [
                'Go to Update folder',
                'Run setup.exe',
                'Follow the on-screen instructions and wait for patching to be finished',
                'Copy crack from RUNE folder to installdir',
                'Play and enjoy!'
            ]
        },
        'TENOKE-Update': {
            type: 'update',
            instructions: [
                'Go to Update folder',
                'Run Patch.exe',
                'Follow the on-screen instructions and wait for patching to be finished',
                'Copy crack to installdir',
                'Play and enjoy!'
            ]
        },
        'Elamigos-Update': {
            type: 'update',
            instructions: [
                'Run the provided exe',
                'Follow the on-screen instructions and wait for patching to be finished',
                'Play and enjoy!'
            ]
        }
    };

    const releaseGroupKeywords = {
        'Dodi': ["DODI", "dodi", "[dodi]", "(dodi)", "(DODI REPACK)", "[DODI REPACK]", "[DODI-REPACK]", "(DODI-REPACK)", "{DODI}", "{DODI REPACK}", "{DODI-Repack}", "DODIRepack"],
        'Fitgirl': ["FitGirl", "Fitgirl", "fitgirl", "[FitGirl]", "(FitGirl)", "{FitGirl}", "FitGirlrepack"],
        'Kaos': ["KaOs", "kaos", "(kaos)", "[kaos]", "[kaos repack]", "[kaos-repack]", "(kaos repack)", "(kaos-repack)", "{kaos-repack}", "{kaos repack}", "kaosrepack"],
        'Elamigos': ["ElAmigos", "ElAmigos", "[ElAmigos]", "(ElAmigos)", "(ElAmigos REPACK)", "[ElAmigos REPACK]", "[ElAmigos-REPACK]", "(ElAmigos-REPACK)", "{ElAmigos}", "{ElAmigos REPACK}", "{ElAmigos-Repack}", "ElAmigosRepack"],
        'RUNE': ["RUNE", "-RUNE", "(RUNE)", "[RUNE]"],
        'FLT': ["FLT", "-FLT", "(FLT)", "[FLT]", "FAIRLIGHT"],
        'TENOKE': ["TENOKE", "-TENOKE", "(TENOKE)", "[TENOKE]"],
        'SKIDROW': ["SKIDROW", "-SKIDROW", "(SKIDROW)", "[SKIDROW]"],
        'TiNYiSO': ["TiNYiSO", "-TiNYiSO", "(TiNYiSO)", "[TiNYiSO]", "TINYISO"],
        'VOICES38': ["VOICES38", "-VOICES38", "(VOICES38)", "[VOICES38]"],
        'GOG': ["GOG", "-GOG", "(GOG)", "[GOG]", "GOG.COM"],
        'SteamBackup': ["[Steam Game Launcher Backup]","Steam Game Backup","[Steam Game Backup]","Steam-Backup","Steam Backup","[Steam Backup]", "(Steam Backup)", "{Steam Backup}", "{Steam-Backup}", "[Steam-Backup]", "(Steam-Backup)"],
        'EpicBackup': ["Epic Games Launcher Backup","[Epic Games Launcher Backup]","[Epic Games Store Backup]","Epic Games Store Backup","Epic-Games-Store-Backup","Epic Backup","Epic Game Backup","[Epic Game Backup]","Epic-Backup","[Epic-Backup]", "(Epic Backup)", "[Epic Backup]", "{Epic Backup}", "Epic Games Backup", "(Epic Games Backup)", "[Epic Games Backup]", "{Epic Games Backup}"],
        'RockstarBackup': ["[Rockstar Games Launcher Backup]","[Rockstar Games Backup]","Rockstar Games Backup","Rockstar Backup", "(Rockstar Backup)", "[Rockstar Backup]", "{Rockstar Backup}", "Rockstar Launcher Backup", "(Rockstar Launcher Backup)", "[Rockstar Launcher Backup]", "{Rockstar Launcher Backup}"],
        'EABackup': ["[EA Backup]","EA Backup","EAOrigin Backup","[EAOrigin Backup]","Origin/EA Backup","[Origin/EA Backup]","EA-Backup", "(EA Backup)", "{EA Backup}","EA/Origin Game Launcher Backup","EA/Origin Game Backup","EA/Origin Backup", "(EA/Origin Backup)", "[EA/Origin Backup]", "{EA/Origin Backup}", "Origin Backup", "(Origin Backup)", "[Origin Backup]", "{Origin Backup}", "EA APP Backup", "(EA APP Backup)", "[EA APP Backup]", "{EA APP Backup}"],
        'UbisoftBackup': ["Ubisoft Connect Backup","Ubisoft Backup","[Ubisoft Connect Files]","[Ubisoft Connect Backup]", "(Ubisoft Connect Backup)", "[Ubisoft Connect Backup]", "{Ubisoft Connect Backup}", "(Ubisoft Backup)", "[Ubisoft Backup]", "{Ubisoft Backup}"],
        'BattleNetBackup': ["[Battle","[Battle Blizzard Backup]","[Battle.net Blizzard Backup]","[Battle.net Backup]","Battle net Files","Battle.net Files","Battle Files","[Battle Files]","Battle net Backup", "(Battle net Backup)", "[Battle net Backup]", "{Battle net Backup}", "Battle.net Backup", "(Battle.net Backup)", "[Battle.net Backup]", "{Battle.net Backup}"],
        'RiotBackup': ["Riot Games Backup","[Riot Games Backup]","(Riot Games Backup)","{Riot Games Backup}","Riot Backup","[Riot Backup]","(Riot Backup)","{Riot Backup}","Riot Games Launcher Backup","[Riot Games Launcher Backup]","(Riot Games Launcher Backup)","{Riot Games Launcher Backup}"],
        'RUNE-Update': ["RUNE Update", "[RUNE Update]", "(RUNE Update)", "{RUNE Update}", "RUNE-Update", "[RUNE-Update]", "(RUNE-Update)", "RUNE.Update", "Update-RUNE", "[Update RUNE]"],
        'TENOKE-Update': ["TENOKE Update", "[TENOKE Update]", "(TENOKE Update)", "{TENOKE Update}", "TENOKE-Update", "[TENOKE-Update]", "(TENOKE-Update)", "TENOKE.Update", "Update-TENOKE", "[Update TENOKE]"],
        'Elamigos-Update': ["ElAmigos Update", "[ElAmigos Update]", "(ElAmigos Update)", "{ElAmigos Update}", "ElAmigos-Update", "[ElAmigos-Update]", "(ElAmigos-Update)", "ElAmigos.Update", "Update-ElAmigos", "[Update ElAmigos]", "Elamigos Update", "Elamigos-Update"]
    };

    function escapeRegExp(string) {
        return string.replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&');
    }

    function detectReleaseGroup(torrentName) {
        const updateKeywords = ['update', 'UPDATE', 'Update'];
        const hasUpdateWord = updateKeywords.some(keyword => torrentName.includes(keyword));

        if (hasUpdateWord) {
            if (/\b(RUNE|-RUNE|\[RUNE\]|\(RUNE\))\b/i.test(torrentName)) return 'RUNE-Update';
            if (/\b(TENOKE|-TENOKE|\[TENOKE\]|\(TENOKE\))\b/i.test(torrentName)) return 'TENOKE-Update';
            if (/\b(ElAmigos|Elamigos|ELAMIGOS|\[ElAmigos\]|\(ElAmigos\)|-ElAmigos)\b/i.test(torrentName)) return 'Elamigos-Update';
        }

        const backupGroups = ['SteamBackup', 'EpicBackup', 'RockstarBackup', 'EABackup', 'UbisoftBackup', 'BattleNetBackup', 'RiotBackup'];
        for (const groupName of backupGroups) {
            const keywords = releaseGroupKeywords[groupName];
            for (const keyword of keywords) {
                const regex = new RegExp(escapeRegExp(keyword), 'i');
                if (regex.test(torrentName)) return groupName;
            }
        }

        for (const [groupName, keywords] of Object.entries(releaseGroupKeywords)) {
            if (groupName.includes('Backup') || groupName.includes('Update')) continue;
            for (const keyword of keywords) {
                const regex = new RegExp(`\\b${escapeRegExp(keyword)}\\b`, 'i');
                if (regex.test(torrentName)) return groupName;
            }
        }

        return DEFAULT_RELEASE_GROUP;
    }

    function isBackupRelease(torrentName) {
        const backupGroups = ['SteamBackup', 'EpicBackup', 'RockstarBackup', 'EABackup', 'UbisoftBackup', 'BattleNetBackup', 'RiotBackup'];
        for (const groupName of backupGroups) {
            const keywords = releaseGroupKeywords[groupName];
            for (const keyword of keywords) {
                const regex = new RegExp(escapeRegExp(keyword), 'i');
                if (regex.test(torrentName)) return true;
            }
        }
        return false;
    }

    const style = document.createElement('style');
    style.textContent = `
        .steam-extractor-panel {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 340px;
            height: 520px;
            background: #0d1117;
            color: #e6edf3;
            border-radius: 8px;
            border: 1px solid #21262d;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            backdrop-filter: blur(10px);
            animation: slideInRight 0.3s ease-out;
        }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .steam-extractor-header {
            padding: 12px 16px;
            border-bottom: 1px solid #21262d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #161b22;
        }
        .steam-extractor-title {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
            color: #e6edf3;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .steam-extractor-title::before {
            content: "🎮";
            font-size: 14px;
        }
        .steam-extractor-close {
            background: #21262d;
            color: #f85149;
            border: 1px solid #30363d;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .steam-extractor-close:hover {
            background: #f85149;
            color: #ffffff;
        }
        .steam-extractor-content {
            padding: 16px;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow: hidden;
        }
        .options-section {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .option-row {
            display: flex;
            gap: 8px;
        }
        .option-group {
            flex: 1;
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 8px;
            transition: all 0.2s ease;
        }
        .option-title {
            font-size: 10px;
            color: #7d8590;
            margin-bottom: 6px;
            font-weight: 500;
            text-transform: uppercase;
        }
        .toggle-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .toggle-label {
            font-size: 12px;
            font-weight: 500;
            color: #e6edf3;
            min-width: 40px;
        }
        .toggle-switch {
            position: relative;
            width: 36px;
            height: 20px;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #21262d;
            border: 1px solid #30363d;
            transition: 0.3s;
            border-radius: 20px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 12px;
            width: 12px;
            left: 3px;
            bottom: 3px;
            background: #ffffff;
            transition: 0.3s;
            border-radius: 50%;
        }
        input:checked + .slider { background: #238636; border-color: #238636; }
        input:checked + .slider:before { transform: translateX(16px); }
        .release-dropdown {
            width: 100%;
            background: #0d1117;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 12px;
            font-family: inherit;
            cursor: pointer;
        }
        .steam-extractor-button {
            background: linear-gradient(135deg, #238636 0%, #196127 100%);
            color: #ffffff;
            border: 1px solid #238636;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
        }
        .steam-extractor-button:hover {
            background: linear-gradient(135deg, #2ea043 0%, #238636 100%);
            transform: translateY(-1px);
        }
        .steam-extractor-button.copy-button {
            background: linear-gradient(135deg, #0969da 0%, #0550ae 100%);
            border-color: #0969da;
        }
        .steam-extractor-button.copy-button:hover {
            background: linear-gradient(135deg, #1f73e6 0%, #0969da 100%);
        }
        .processing-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            color: #58a6ff;
            font-size: 11px;
            min-height: 16px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .processing-indicator.visible { opacity: 1; }
        .processing-indicator::before {
            content: "";
            width: 10px;
            height: 10px;
            border: 2px solid transparent;
            border-top-color: #58a6ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        .steam-extractor-textarea {
            flex: 1;
            background: #0d1117;
            color: #e6edf3;
            border: 1px solid #21262d;
            border-radius: 4px;
            padding: 8px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 10px;
            line-height: 1.3;
            resize: none;
            outline: none;
            transition: all 0.2s ease;
            min-height: 140px;
        }
        .steam-extractor-textarea:focus { border-color: #58a6ff; }
        .steam-extractor-textarea::placeholder { color: #7d8590; font-style: italic; }
        .steam-extractor-textarea::-webkit-scrollbar { width: 8px; }
        .steam-extractor-textarea::-webkit-scrollbar-track { background: #161b22; border-radius: 4px; }
        .steam-extractor-textarea::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
        .steam-extractor-textarea::-webkit-scrollbar-thumb:hover { background: #484f58; }
        .success-feedback {
            background: linear-gradient(135deg, #238636 0%, #196127 100%) !important;
            color: #ffffff !important;
        }
        .steam-extractor-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            background: #0d1117;
            color: #58a6ff;
            border: 1px solid #21262d;
            border-radius: 8px;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            z-index: 9998;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            transition: all 0.2s ease;
        }
        .steam-extractor-toggle:hover {
            background: #161b22;
            color: #79c0ff;
            transform: scale(1.05);
        }
        .steam-extractor-toggle.show { display: flex; }
        .tbd-game-desc-button {
            background: transparent;
            color: inherit;
            border: 1px solid;
            border-color: inherit;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 11px;
            font-weight: normal;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
            margin-right: 2px;
            height: auto;
            display: inline-block;
            vertical-align: middle;
            line-height: normal;
        }
        .tbd-game-desc-button:hover { opacity: 0.8; }
        .tbd-game-desc-button:active { opacity: 0.6; }
        .tbd-processing-overlay {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999999;
            animation: slideInUp 0.3s ease-out;
        }
        @keyframes slideInUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .tbd-processing-content {
            background: rgba(26, 26, 46, 0.95);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            min-width: 240px;
        }
        .tbd-processing-spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(59, 130, 246, 0.2);
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            flex-shrink: 0;
        }
        .tbd-processing-text-container { display: flex; flex-direction: column; gap: 2px; }
        .tbd-processing-text {
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            line-height: 1.3;
        }
        .tbd-processing-subtext {
            color: #94a3b8;
            font-size: 11px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            line-height: 1.3;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    let toggleButton;
    if (isSteamPage) {
        toggleButton = document.createElement('div');
        toggleButton.className = 'steam-extractor-toggle';
        toggleButton.innerHTML = '🎮';
        toggleButton.title = 'Open Steam Extractor';
        document.body.appendChild(toggleButton);
    }

    let panel;
    if (isSteamPage) {
        panel = document.createElement('div');
        panel.className = 'steam-extractor-panel';
        panel.innerHTML = `
            <div class="steam-extractor-header">
                <h4 class="steam-extractor-title">Steam Extractor</h4>
                <button class="steam-extractor-close" onclick="document.querySelector('.steam-extractor-panel').style.display='none'; document.querySelector('.steam-extractor-toggle').classList.add('show');">×</button>
            </div>
            <div class="steam-extractor-content">
                <div class="options-section">
                    <div class="option-row">
                        <div class="option-group">
                            <div class="option-title">Release Type</div>
                            <div class="toggle-container">
                                <span class="toggle-label" id="type-label">Repack</span>
                                <label class="toggle-switch">
                                    <input type="checkbox" id="type-toggle">
                                    <span class="slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="option-group" id="release-container">
                        <div class="option-title">Release Group</div>
                        <select class="release-dropdown" id="release-dropdown">
                            <optgroup label="Repack Groups">
                                <option value="Dodi">Dodi</option>
                                <option value="Fitgirl">Fitgirl</option>
                                <option value="Elamigos">Elamigos</option>
                                <option value="Kaos">Kaos</option>
                            </optgroup>
                            <optgroup label="Scene Groups">
                                <option value="RUNE">RUNE</option>
                                <option value="VOICES38">VOICES38</option>
                                <option value="FLT">FLT</option>
                                <option value="TENOKE">TENOKE</option>
                                <option value="SKIDROW">SKIDROW</option>
                                <option value="TiNYiSO">TiNYiSO</option>
                                <option value="GOG">GOG</option>
                            </optgroup>
                        </select>
                    </div>
                </div>
                <button class="steam-extractor-button" id="extract-complete">Extract Game Description</button>
                <div class="processing-indicator" id="processing-status"></div>
                <textarea class="steam-extractor-textarea" id="extracted-content" placeholder="Extracted game description will appear here..."></textarea>
                <button class="steam-extractor-button copy-button" id="copy-content">Copy to Clipboard</button>
            </div>
        `;
        document.body.appendChild(panel);

        const typeToggle = document.getElementById('type-toggle');
        const typeLabel = document.getElementById('type-label');
        const releaseDropdown = document.getElementById('release-dropdown');

        typeToggle.addEventListener('change', function() {
            typeLabel.textContent = this.checked ? 'Scene' : 'Repack';
            typeLabel.style.color = this.checked ? '#a855f7' : '#58a6ff';
            updateReleaseDropdown();
        });

        function updateReleaseDropdown() {
            const isScene = typeToggle.checked;
            releaseDropdown.innerHTML = '';
            if (isScene) {
                const sceneGroup = document.createElement('optgroup');
                sceneGroup.label = 'Scene Groups';
                ['RUNE', 'FLT', 'TENOKE', 'SKIDROW', 'TiNYiSO', 'VOICES38', 'GOG'].forEach(group => {
                    const option = document.createElement('option');
                    option.value = group;
                    option.textContent = group;
                    sceneGroup.appendChild(option);
                });
                releaseDropdown.appendChild(sceneGroup);
                releaseDropdown.value = 'RUNE';
            } else {
                const repackGroup = document.createElement('optgroup');
                repackGroup.label = 'Repack Groups';
                ['Dodi', 'Fitgirl', 'Elamigos', 'Kaos'].forEach(group => {
                    const option = document.createElement('option');
                    option.value = group;
                    option.textContent = group;
                    repackGroup.appendChild(option);
                });
                releaseDropdown.appendChild(repackGroup);
                releaseDropdown.value = 'Dodi';
            }
        }

        function setDefaultReleaseGroup() {
            if (releaseGroups[DEFAULT_RELEASE_GROUP]) {
                const groupType = releaseGroups[DEFAULT_RELEASE_GROUP].type;
                if (groupType === 'scene') {
                    typeToggle.checked = true;
                    typeLabel.textContent = 'Scene';
                    typeLabel.style.color = '#a855f7';
                } else {
                    typeToggle.checked = false;
                    typeLabel.textContent = 'Repack';
                    typeLabel.style.color = '#58a6ff';
                }
                updateReleaseDropdown();
                releaseDropdown.value = DEFAULT_RELEASE_GROUP;
            }
        }

        setDefaultReleaseGroup();

        toggleButton.addEventListener('click', function() {
            panel.style.display = 'flex';
            toggleButton.classList.remove('show');
        });
    }

    if (isTBDUploadPage) {
        const tbdButton = document.createElement("div");
        tbdButton.classList.add('bbc-btn', 'tbd-game-desc-button');
        tbdButton.setAttribute('title', 'Extract Game Description from Steam');
        tbdButton.textContent = 'GAME DESC';

        function hasReleaseGroup(torrentName) {
            if (!torrentName) return false;
            for (const [groupName, keywords] of Object.entries(releaseGroupKeywords)) {
                for (const keyword of keywords) {
                    const regex = new RegExp(escapeRegExp(keyword), 'i');
                    if (regex.test(torrentName)) return true;
                }
            }
            return false;
        }

        function autoSelectAndShowButton() {
            const torrentNameInput = document.querySelector('#torrent_name');
            const categorySelect = document.querySelector('select[name="type"]');
            const languageSelect = document.querySelector('select[name="lang"]');
            if (!torrentNameInput || !categorySelect || !languageSelect) return;

            const torrentName = torrentNameInput.value.trim();
            if (hasReleaseGroup(torrentName)) {
                const detectedGroup = detectReleaseGroup(torrentName);
                if (detectedGroup && detectedGroup.includes('Update')) {
                    categorySelect.value = "52";
                } else if (isBackupRelease(torrentName)) {
                    categorySelect.value = "81";
                } else {
                    categorySelect.value = "10";
                }
                categorySelect.dispatchEvent(new Event('change', { bubbles: true }));
                languageSelect.value = "1";
                if (!tbdButton.parentNode) {
                    const uploadMediaInfoButton = document.querySelector('.bbc-more-contents');
                    if (uploadMediaInfoButton) {
                        uploadMediaInfoButton.parentNode.insertBefore(tbdButton, uploadMediaInfoButton.nextSibling);
                    }
                }
            } else {
                if (tbdButton.parentNode) tbdButton.parentNode.removeChild(tbdButton);
            }
        }

        function checkCategoryAndDisplayButton() {
            const categorySelect = document.querySelector('select[name="type"]');
            const selectedCategory = categorySelect ? parseInt(categorySelect.value) : null;
            const validCategories = [10, 60, 52, 81];
            if (validCategories.includes(selectedCategory)) {
                if (!tbdButton.parentNode) {
                    const uploadMediaInfoButton = document.querySelector('.bbc-more-contents');
                    if (uploadMediaInfoButton) {
                        uploadMediaInfoButton.parentNode.insertBefore(tbdButton, uploadMediaInfoButton.nextSibling);
                    }
                }
            } else {
                if (tbdButton.parentNode) tbdButton.parentNode.removeChild(tbdButton);
            }
        }

        const torrentNameInput = document.querySelector('#torrent_name');
        if (torrentNameInput) {
            torrentNameInput.addEventListener('input', autoSelectAndShowButton);
            torrentNameInput.addEventListener('change', autoSelectAndShowButton);
            torrentNameInput.addEventListener('paste', function() { setTimeout(autoSelectAndShowButton, 100); });
            setTimeout(autoSelectAndShowButton, 500);
        }

        const categorySelect = document.querySelector('select[name="type"]');
        if (categorySelect) categorySelect.addEventListener('change', checkCategoryAndDisplayButton);

        checkCategoryAndDisplayButton();

        tbdButton.addEventListener('click', function() {
            const categorySelect = document.querySelector('select[name="type"]');
            const torrentNameInput = document.querySelector('#torrent_name');
            const selectedCategory = categorySelect ? categorySelect.value : null;
            const torrentName = torrentNameInput ? torrentNameInput.value : '';

            if (selectedCategory === '81' || selectedCategory === '10' || selectedCategory === '60' || selectedCategory === '52') {
                const languageSelect = document.querySelector('select[name="lang"]');
                if (languageSelect) languageSelect.value = "1";

                let cleanTorrentName = torrentName;
                cleanTorrentName = cleanTorrentName.replace(/\s*[\[\(].*?(FitGirl|DODI|Kaos|ElAmigos|RUNE|FLT|TENOKE|SKIDROW|TiNYiSO|GOG|Steam|Epic|Rockstar|EA|Ubisoft|Battle|Riot).*?[\]\)].*$/i, '');
                cleanTorrentName = cleanTorrentName.replace(/\s*-\s*(RUNE|FLT|TENOKE|SKIDROW|TiNYiSO|FAIRLIGHT|GOG)$/i, '');
                cleanTorrentName = cleanTorrentName.replace(/\s+v\.?\d+.*$/i, '');

                const patterns = [
                    / SEASON\s+\d+.*$/i,
                    / Chapter\s+\d+.*$/i,
                    /Episode\s+\d+.*$/i,
                    / Build\s+\d+.*$/i,
                    /\s+update.*$/i,
                ];

                let previousName;
                do {
                    previousName = cleanTorrentName;
                    for (let pattern of patterns) cleanTorrentName = cleanTorrentName.replace(pattern, '');
                    cleanTorrentName = cleanTorrentName.trim();
                } while (cleanTorrentName !== previousName);

                const detectedReleaseGroup = detectReleaseGroup(torrentName);
                const searchQuery = encodeURIComponent(`${cleanTorrentName} Steam link`);
                const googleSearchUrl = `https://www.google.com/search?q=${searchQuery}`;

                showTBDProcessingPopup();

                GM_xmlhttpRequest({
                    method: 'GET',
                    url: googleSearchUrl,
                    onload: function(response) {
                        if (response.status === 200) {
                            if (response.responseText.includes('captcha') || response.responseText.includes('human verification')) {
                                alert('Google requires human verification or CAPTCHA. Please verify manually.');
                                window.open(googleSearchUrl, '_blank');
                                hideTBDProcessingPopup();
                                return;
                            }
                            const steamLinkMatch = response.responseText.match(/https:\/\/store\.steampowered\.com\/app\/\d+\/[^"]+/);
                            if (steamLinkMatch) {
                                const appIdMatch = steamLinkMatch[0].match(/app\/(\d+)/);
                                if (appIdMatch) {
                                    fetchSteamDataForTBD(appIdMatch[1], detectedReleaseGroup, function(finalBBCode) {
                                        const descriptionTextArea = document.querySelector('#torr-descr[name="descr"]');
                                        if (descriptionTextArea) {
                                            descriptionTextArea.value = finalBBCode;
                                        } else {
                                            alert('Could not find the description text area.');
                                        }
                                        hideTBDProcessingPopup();
                                    });
                                } else {
                                    alert('Invalid Steam link format. Could not extract AppID.');
                                    hideTBDProcessingPopup();
                                }
                            } else {
                                alert('Game not found on Steam. Visit the Steam page and extract the description manually.');
                                hideTBDProcessingPopup();
                            }
                        } else {
                            if (response.responseText.includes('captcha') || response.responseText.includes('human verification')) {
                                alert('Google requires human verification or CAPTCHA. Please verify manually.');
                                window.open(googleSearchUrl, '_blank');
                            } else {
                                alert('Failed to search Google');
                            }
                            hideTBDProcessingPopup();
                        }
                    },
                    onerror: function(error) {
                        console.error('Error performing Google search:', error);
                        alert('An error occurred while performing the Google search.');
                        hideTBDProcessingPopup();
                    }
                });
            } else {
                alert('Please select a valid Game Category');
            }
        });

        function showTBDProcessingPopup() {
            const processingOverlay = document.createElement('div');
            processingOverlay.id = 'tbdProcessingOverlay';
            processingOverlay.className = 'tbd-processing-overlay';
            processingOverlay.innerHTML = `
                <div class="tbd-processing-content">
                    <div class="tbd-processing-spinner"></div>
                    <div class="tbd-processing-text-container">
                        <div class="tbd-processing-text">Processing Game Description</div>
                        <div class="tbd-processing-subtext">Extracting from Steam...</div>
                    </div>
                </div>
            `;
            document.body.appendChild(processingOverlay);
        }

        function hideTBDProcessingPopup() {
            const processingOverlay = document.querySelector('#tbdProcessingOverlay');
            if (processingOverlay) {
                processingOverlay.style.opacity = '0';
                processingOverlay.style.transform = 'translateY(100%)';
                setTimeout(() => {
                    if (processingOverlay.parentNode) document.body.removeChild(processingOverlay);
                }, 300);
            }
        }
    }

    function copyToClipboard(text) {
        const textarea = document.getElementById('extracted-content');
        textarea.value = text;
        textarea.select();
        document.execCommand('copy');
        const copyBtn = document.getElementById('copy-content');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = 'Copied Successfully!';
        copyBtn.classList.add('success-feedback');
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove('success-feedback');
        }, 2000);
    }

    function extractGameNameAndYouTubeTrailer(gameName, callback) {
        var apiKeyIndex = 0;
        function searchTrailer(cb) {
            if (apiKeyIndex >= combinedYoutubeApiKeys.length) { cb(null); return; }
            var apiKey = combinedYoutubeApiKeys[apiKeyIndex];
            var searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q=${encodeURIComponent(gameName + ' game trailer')}&key=${apiKey}&maxResults=1`;
            GM_xmlhttpRequest({
                method: 'GET',
                url: searchUrl,
                onload: function(searchResponse) {
                    if (searchResponse.status === 200) {
                        var searchResults = JSON.parse(searchResponse.responseText);
                        if (searchResults.items && searchResults.items.length > 0) {
                            cb(`[video=https://www.youtube.com/watch?v=${searchResults.items[0].id.videoId}]`);
                        } else { apiKeyIndex++; searchTrailer(cb); }
                    } else { apiKeyIndex++; searchTrailer(cb); }
                },
                onerror: function() { apiKeyIndex++; searchTrailer(cb); }
            });
        }
        searchTrailer(function(result) { callback(result); });
    }

    function getAppId() {
        const match = window.location.pathname.match(/app\/(\d+)/);
        return match ? match[1] : null;
    }

    function generateCompleteDescription(info, selectedReleaseGroup) {
        const isGOG = selectedReleaseGroup === 'GOG';
        const isBackup = releaseGroups[selectedReleaseGroup] && releaseGroups[selectedReleaseGroup].type === 'backup';

        const protectionMap = {
            'GOG': 'NO PROTECTION',
            'SteamBackup': 'STEAM',
            'EpicBackup': 'EPIC ONLINE SERVICES',
            'RockstarBackup': 'ROCKSTAR SOCIAL CLUB',
            'EABackup': 'EA APP',
            'UbisoftBackup': 'UBISOFT CONNECT',
            'BattleNetBackup': 'BATTLE.NET',
            'RiotBackup': 'RIOT CLIENT',
            'RUNE-Update': 'STEAM',
            'TENOKE-Update': 'STEAM',
            'Elamigos-Update': 'STEAM'
        };
        if (protectionMap[selectedReleaseGroup]) info.protection = protectionMap[selectedReleaseGroup];

        let bbcode = '';
        if (CUSTOM_TOP_MESSAGE && CUSTOM_TOP_MESSAGE.trim() !== '') bbcode += `${CUSTOM_TOP_MESSAGE}\n\n`;

        bbcode += '[font=Consolas]';
        bbcode += `[center][img]${info.headerImage}[/img][/center]\n`;
        if (info.title) bbcode += `\n[center][size=5][color=orange]${info.title}[/color][/size][/center]\n`;

        bbcode += `\n[img]${getImageUrl('info', isGOG)}[/img]\n\n`;
        bbcode += `[color=magenta]Type:...............[/color] ${info.type}\n`;

        if (info.genres.length > 0) {
            bbcode += `[color=magenta]Genre:..............[/color] ${info.genres.map(g => `[url=${g.url}]${g.text}[/url]`).join(', ')}\n`;
        }
        if (info.publishers.length > 0) {
            bbcode += `[color=magenta]Publisher:..........[/color] ${info.publishers.map(p => `[url=${p.url}]${p.text}[/url]`).join(', ')}\n`;
        }
        if (info.website) bbcode += `[color=magenta]Website:............[/color] ${info.website}\n`;
        if (info.releaseDate) bbcode += `[color=magenta]Release date:.......[/color] ${info.releaseDate}\n`;

        bbcode += `[color=magenta]Price:..............[/color] ${info.price}\n`;
        bbcode += `[color=magenta]Url:................[/color] [url=${info.url}]${info.url}[/url]\n`;

        const windowsIcon = info.platforms.windows ? `[img]${defaultImages.checkedIcon}[/img]` : `[img]${defaultImages.uncheckedIcon}[/img]`;
        const macIcon = info.platforms.mac ? `[img]${defaultImages.checkedIcon}[/img]` : `[img]${defaultImages.uncheckedIcon}[/img]`;
        const linuxIcon = info.platforms.linux ? `[img]${defaultImages.checkedIcon}[/img]` : `[img]${defaultImages.uncheckedIcon}[/img]`;
        bbcode += `[color=magenta]Platforms:..........[/color] Windows:${windowsIcon} MacOSX:${macIcon} Linux:${linuxIcon}\n`;

        if (info.languages.length > 0) bbcode += `[color=magenta]Languages:..........[/color] ${info.languages.join(', ')}\n`;
        bbcode += `[color=magenta]Protection..........[/color] ${info.protection}\n`;
        bbcode += '\n';

        bbcode += `[img]${getImageUrl('description')}[/img]\n\n`;
        if (info.description) bbcode += `${info.description}\n\n`;

        bbcode += `[img]${getImageUrl('requirements')}[/img]\n\n`;
        if (info.systemRequirements) bbcode += `${info.systemRequirements}\n\n`;

        bbcode += `[img]${getImageUrl('installNotes')}[/img]\n\n`;

        const releaseGroup = releaseGroups[selectedReleaseGroup];
        if (releaseGroup) {
            releaseGroup.instructions.forEach(instruction => { bbcode += `➩ ${instruction}\n`; });
            bbcode += `\nNOTES\n`;
            if (isBackup) {
                bbcode += `➩ Don't seed and play from the same folder, it will cause network issues and possible FPS issues; and future updates will cause errors in seeding\n`;
            } else {
                bbcode += `➩ Don't forget to add an exception to your antivirus (if required)\n➩ Block all game executables in your firewall\n`;
            }
            bbcode += '\n';
        }

        bbcode += `[img]${getImageUrl('screenshots')}[/img]\n\n`;
        bbcode += `[center]\n`;
        info.screenshots.forEach(screenshot => { bbcode += `[img]${screenshot}[/img]\n`; });
        bbcode += `[/center]\n`;

        if (info.trailer && info.trailer.trim() !== '') {
            bbcode += `\n[img]${getImageUrl('trailer')}[/img]\n\n`;
            bbcode += `[center]${info.trailer}\n[/center]\n\n`;
        }

        bbcode += '[/font]';
        if (CUSTOM_BOTTOM_MESSAGE && CUSTOM_BOTTOM_MESSAGE.trim() !== '') bbcode += `\n\n${CUSTOM_BOTTOM_MESSAGE}`;

        return bbcode;
    }

    function fetchSteamDataForTBD(appId, releaseGroup, callback) {
        GM_xmlhttpRequest({
            method: 'GET',
            url: `https://store.steampowered.com/api/appdetails?appids=${appId}&cc=us&l=en`,
            onload: function(response) {
                if (response.status === 200) {
                    let apiData;
                    try {
                        apiData = JSON.parse(response.responseText);
                    } catch (e) {
                        alert('Failed to parse Steam API response.');
                        callback('', null);
                        return;
                    }

                    if (!apiData[appId] || !apiData[appId].success) {
                        alert('Steam API returned no data for this game.');
                        callback('', null);
                        return;
                    }

                    const data = apiData[appId].data;

                    const info = {
                        appId: appId,
                        title: data.name || '',
                        headerImage: (data.header_image || `https://cdn.akamai.steamstatic.com/steam/apps/${appId}/header.jpg`).split('?')[0],
                        type: data.type ? data.type.charAt(0).toUpperCase() + data.type.slice(1) : 'Game',
                        genres: (data.genres || []).map(g => ({
                            text: g.description,
                            url: `https://store.steampowered.com/genre/${encodeURIComponent(g.description)}/`
                        })),
                        developers: (data.developers || []).map(d => ({
                            text: d,
                            url: `https://store.steampowered.com/search/?developer=${encodeURIComponent(d)}`
                        })),
                        publishers: (data.publishers || []).map(p => ({
                            text: p,
                            url: `https://store.steampowered.com/search/?publisher=${encodeURIComponent(p)}`
                        })),
                        website: data.website || '',
                        releaseDate: (data.release_date && data.release_date.date) ? data.release_date.date : '',
                        price: (data.price_overview && data.price_overview.final_formatted)
                            ? data.price_overview.final_formatted
                            : (data.is_free ? 'Free' : 'No price found'),
                        url: `https://store.steampowered.com/app/${appId}`,
                        platforms: {
                            windows: (data.platforms && data.platforms.windows) || false,
                            mac: (data.platforms && data.platforms.mac) || false,
                            linux: (data.platforms && data.platforms.linux) || false
                        },
                        languages: [],
                        protection: releaseGroup === 'GOG' ? 'NO PROTECTION' : 'STEAM',
                        description: data.short_description || '',
                        systemRequirements: '',
                        screenshots: (data.screenshots || []).map(s => {
                            let url = s.path_full;
                            url = url.replace(/https:\/\/[^\/]*steamstatic\.com/, 'https://shared.akamai.steamstatic.com');
                            url = url.split('?')[0];
                            return url;
                        }),
                        trailer: ''
                    };

                    if (data.supported_languages) {
                        const langHtml = data.supported_languages.split('<br>')[0];
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = langHtml;
                        const rawText = tempDiv.textContent || tempDiv.innerText || '';
                        info.languages = rawText
                            .split(',')
                            .map(l => l.replace(/\*/g, '').trim())
                            .filter(l => l.length > 0);
                    }

                    if (data.pc_requirements && data.pc_requirements.minimum) {
                        const combinedHtml = (data.pc_requirements.minimum || '') + (data.pc_requirements.recommended || '');
                        let sysReq = combinedHtml
                            .replace(/<br\s*[\/]?>/gi, '\n')
                            .replace(/<li>/gi, '')
                            .replace(/<\/li>/gi, '\n')
                            .replace(/<ul[^>]*>/gi, '')
                            .replace(/<\/ul>/gi, '')
                            .replace(/<strong>(.*?)<\/strong>/gi, '$1')
                            .replace(/<\/?[^>]+(>|$)/g, '');

                        sysReq = sysReq
                            .replace(/Minimum:/gi, '[b]Minimum:[/b]')
                            .replace(/Recommended:/gi, '\n\n[b]Recommended:[/b]')
                            .replace(/Requires a 64-bit processor and operating system/gi, '')
                            .replace(/OS\s*\*?:/gi, '\n➩ [b]OS:[/b]')
                            .replace(/Processor:/gi, '\n➩ [b]Processor:[/b]')
                            .replace(/Memory:/gi, '\n➩ [b]Memory:[/b]')
                            .replace(/Graphics:/gi, '\n➩ [b]Graphics:[/b]')
                            .replace(/DirectX:/gi, '\n➩ [b]DirectX:[/b]')
                            .replace(/DirectX®:/gi, '\n➩ [b]DirectX:[/b]')
                            .replace(/Storage:/gi, '\n➩ [b]Storage:[/b]')
                            .replace(/Hard Drive:/gi, '\n➩ [b]Storage:[/b]')
                            .replace(/Sound Card:/gi, '\n➩ [b]Sound Card:[/b]')
                            .replace(/Sound:/gi, '\n➩ [b]Sound Card:[/b]')
                            .replace(/Network:/gi, '\n➩ [b]Network:[/b]')
                            .replace(/VR Support:/gi, '\n➩ [b]VR Support:[/b]')
                            .replace(/VR:/gi, '\n➩ [b]VR Support:[/b]')
                            .replace(/Other Requirements:/gi, '\n➩ [b]Other Requirements:[/b]')
                            .replace(/Additional Notes:/gi, '\n➩ [b]Additional Notes:[/b]')
                            .replace(/Additional:/gi, '\n➩ [b]Additional:[/b]')
                            .replace(/\n\s*\n/g, '\n')
                            .trim();

                        const parts = sysReq.split('[b]Recommended:[/b]');
                        if (parts.length === 2 && !parts[1].trim()) sysReq = parts[0].trim();

                        info.systemRequirements = sysReq;
                    } else {
                        info.systemRequirements = 'No system requirements available.';
                    }

                    function finalize() {
                        const protectionMap = {
                            'GOG': 'NO PROTECTION',
                            'SteamBackup': 'STEAM',
                            'EpicBackup': 'EPIC ONLINE SERVICES',
                            'RockstarBackup': 'ROCKSTAR SOCIAL CLUB',
                            'EABackup': 'EA APP',
                            'UbisoftBackup': 'UBISOFT CONNECT',
                            'BattleNetBackup': 'BATTLE.NET',
                            'RiotBackup': 'RIOT CLIENT'
                        };
                        if (protectionMap[releaseGroup]) info.protection = protectionMap[releaseGroup];

                        const hasDenuvo = data.drm_notice && /denuvo/i.test(data.drm_notice);
                        if (hasDenuvo && !protectionMap[releaseGroup]) info.protection = 'DENUVO & STEAM';

                        if (info.title) {
                            extractGameNameAndYouTubeTrailer(info.title, function(trailer) {
                                if (trailer) info.trailer = trailer;
                                const completeDescription = generateCompleteDescription(info, releaseGroup);
                                callback(completeDescription, info);
                            });
                        } else {
                            const completeDescription = generateCompleteDescription(info, releaseGroup);
                            callback(completeDescription, info);
                        }
                    }

                    finalize();

                } else {
                    alert('Failed to fetch Steam API data.');
                    callback('', null);
                }
            },
            onerror: function(error) {
                console.error('Error fetching Steam API:', error);
                alert('An error occurred while fetching Steam data.');
                callback('', null);
            }
        });
    }

    let cachedGameInfo = null;
    let currentAppId = null;

    function extractCompleteDescription() {
        if (!isSteamPage) return;

        const statusElement = document.getElementById('processing-status');
        const extractBtn = document.getElementById('extract-complete');
        const appId = getAppId();
        const selectedReleaseGroup = document.getElementById('release-dropdown').value;

        if (cachedGameInfo && currentAppId === appId) {
            const completeDescription = generateCompleteDescription(cachedGameInfo, selectedReleaseGroup);
            document.getElementById('extracted-content').value = completeDescription;
            return;
        }

        statusElement.textContent = 'Fetching game data...';
        statusElement.classList.add('visible');
        extractBtn.disabled = true;
        extractBtn.style.opacity = '0.6';

        setTimeout(() => {
            try {
                fetchSteamDataForTBD(appId, selectedReleaseGroup, function(finalBBCode, gameInfo) {
                    if (finalBBCode) {
                        cachedGameInfo = gameInfo;
                        currentAppId = appId;
                        document.getElementById('extracted-content').value = finalBBCode;
                    } else {
                        statusElement.textContent = 'Failed to extract game description';
                        statusElement.style.color = '#f85149';
                    }
                    statusElement.classList.remove('visible');
                    extractBtn.disabled = false;
                    extractBtn.style.opacity = '1';
                });
            } catch (error) {
                console.error('Extraction error:', error);
                statusElement.textContent = 'Error during extraction';
                statusElement.style.color = '#f85149';
                document.getElementById('extracted-content').value = 'Error occurred during extraction. Check console for details.';
                extractBtn.disabled = false;
                extractBtn.style.opacity = '1';
            }
        }, 100);
    }

    if (isSteamPage) {
        document.getElementById('extract-complete').addEventListener('click', extractCompleteDescription);

        document.getElementById('release-dropdown').addEventListener('change', function() {
            if (cachedGameInfo) extractCompleteDescription();
        });

        document.getElementById('type-toggle').addEventListener('change', function() {
            if (cachedGameInfo) setTimeout(extractCompleteDescription, 50);
        });

        document.getElementById('copy-content').addEventListener('click', function() {
            const content = document.getElementById('extracted-content').value;
            if (content) copyToClipboard(content);
        });

        panel.style.display = 'none';
        toggleButton.classList.add('show');
        setTimeout(extractCompleteDescription, 2000);
    }

})();