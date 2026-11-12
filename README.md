# Anan Reel Edit — Claude Code Skill

A Claude Code skill for editing Anan's Bangla/Banglish trading & finance reels (2160x3840 @ 25fps)
in Premiere Pro + After Effects (+ Remotion for explainers): transcription, cuts, captions, 3D camera
rig, cards, SFX, music mix and 80 Mbps render preset.

## Install on a new PC

**Windows (PowerShell or Git Bash):**

```bash
git clone https://github.com/tarzo-codes/anan-reel-edit-skill.git "$HOME/.claude/skills/anan-reel-edit"
```

Restart Claude Code — the skill shows up as `anan-reel-edit`.

## Update to the latest version

```bash
git -C "$HOME/.claude/skills/anan-reel-edit" pull
```

## Requirements

- Claude Code with the Premiere Pro and After Effects MCP servers
- Python 3.12, ffmpeg, Node.js (for Remotion explainers)
- Fonts: Plus Jakarta Sans, Syne, Anton, Bebas Neue, Instrument Serif, JetBrains Mono, Hind Siliguri
- Optional: `PEXELS_API_KEY` / `PIXABAY_API_KEY` in env or `E:/Anan/.env` for stock downloads

## Folder paths

The scripts expect the original layout: `E:\Anan\NEW` (raw videos), `E:\Anan\Assets` (fonts, AE projects),
`D:\Assets\01_Audio\SFX` (SFX). On a new PC, use the same drive layout or ask Claude to update the paths.

Premiere export preset: `assets/Anan Reel 4K H264 80Mbps.epr` — import it in Premiere's Export window.
