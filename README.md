# Anan Reel Edit — Claude Code Skill

A Claude Code skill for editing Anan's Bangla/Banglish trading & finance reels (2160x3840 @ 25fps)
in Premiere Pro + After Effects (+ Remotion for explainers): transcription, cuts, captions, 3D camera
rig, cards, SFX, music mix and 80 Mbps render preset.

## What kind of videos it makes

Short vertical **Bangla / Banglish trading & money reels** for TikTok, Instagram Reels, YouTube Shorts and Facebook,
built from a creator's raw talking-head or handheld selfie clips. 4K vertical (2160x3840, 25 fps), MP4.

**The look**
- **Simple, credible "trader at the desk" style:** the creator on camera with charts behind, plain big bold text,
  numbers in **green**, warnings in **red**. No ad-template look.
- **Fixed money header** across the top for the whole reel: one concrete promise or hook
  (e.g. "২ হাজার -> 30-40 হাজার", "99% Failure", "How to make money?"), shown and said in the first 2 seconds.
- **Bangla captions** in 3-4-word chunks that land on the spoken word, low on screen; English trading words stay in English.
- **Fast, literal B-roll** (1-2 s): money, charts, stressed trader, gym, roulette, hourglass — always matching the exact
  word being said. Pulled automatically from Pexels / Pixabay or the creator's own clips.
- **Pop elements:** numbered step badges in animated circles, green/red number pops, big animated emojis and money
  bursts behind a cut-out of the speaker, a typing TikTok/YouTube comment box as the call to action, tick / cross impacts.
- **Camera punches:** quick 100 -> 110-118 % zooms on key words instead of slow pushes.
- **Sound:** clean zero-vocal instrumental music under the voice (voice at -15 LUFS, music 10 LU under), stop-drops on
  big lines, layered whoosh / click / ding SFX, limiter on every track.

**Formats**
- **Talking reels, 30-40 s** — hook -> point -> proof -> lesson -> CTA. The main format.
- **Lifestyle POV shorts, 9-21 s** — cash on the desk, travel, airport; music only with one "POV:" header.
- **Funny news / gossip reels** — meme-style edits with up to three music beds by mood.
- **Explainer inserts** — animated charts and terminal visuals rendered with Remotion.

**Three vibes** you pick per reel:
| Vibe | What you get |
|---|---|
| **Simple** | Captions, a few text pops / PNGs / stock, clean cuts and zooms |
| **Casual** | The normal house style above (default) |
| **Extreme** | Fast cuts every ~2 s, heavy animation, 3D After Effects camera scenes (grid planes, mind-map boards, versus splits) |

The creator's own data shows the **Simple / Casual** look wins; heavy 3D edits are kept only for the Extreme vibe.

**How it works:** cuts first (silences, ums, retakes and false starts removed) -> you review in Premiere ->
full edit in the chosen vibe -> Claude checks frames and the mix -> renders 80 Mbps MP4s through Media Encoder.

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
