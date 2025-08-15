#!/usr/bin/env python3
import json, argparse, pathlib
from string import Template

def to_ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h  = cs // 360000
    m  = (cs // 6000) % 60
    s  = (cs // 100) % 60
    c  = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

def esc(s: str) -> str:
    return s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")

def rgb_to_ass_hex(rgb: str) -> str:
    """#RRGGBB -> AABBGGRR (AA=00 opaque) w/o &H"""
    rgb = rgb.lstrip("#")
    r = int(rgb[0:2], 16); g = int(rgb[2:4], 16); b = int(rgb[4:6], 16)
    return f"00{b:02X}{g:02X}{r:02X}"

def bbggrr(rgb: str) -> str:
    """#RRGGBB -> BBGGRR for inline \\1c&H...&"""
    rgb = rgb.lstrip("#")
    r = int(rgb[0:2], 16); g = int(rgb[2:4], 16); b = int(rgb[4:6], 16)
    return f"{b:02X}{g:02X}{r:02X}"

ASS_HEADER_TPL = Template("""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
; Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,
; Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,
; BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
; Default (inactive) is white; active word color set inline.
Style: Cap,$font,$fs,&H$inactive,&H$inactive,&H$outline,&H64000000,-1,0,0,0,100,100,0,0,1,$bord,$shad,2,$ml,$mr,$mv,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")

def build_line_text(block_words, active_idx, color_active, color_inactive,
                    base_outline, pop_in_ms, pop_out_ms, pop_outline_extra, pop_blur,
                    uppercase=True):
    """
    Active word: inline color + outline/blur pulse via \\t()
    Inactive words: inline white, base outline, no animation.
    """
    parts = [r"{\q2}{\fsp2}"]  # better wrapping + slight spacing

    active_color   = bbggrr(color_active)
    inactive_color = bbggrr(color_inactive)

    # timings (ms) within this dialogue event
    t1 = max(0, pop_in_ms)
    t2 = max(t1, pop_out_ms)

    for i, w in enumerate(block_words):
        txt = str(w["word"])
        if uppercase: txt = txt.upper()
        if i == active_idx:
            # start at base look, pulse outline/blur, then settle back
            tag = (f"{{\\rCap\\1c&H{active_color}&\\bord{base_outline}\\blur0"
                   + (f"\\t(0,{t1},\\bord{base_outline + pop_outline_extra}\\blur{pop_blur})" if t1 > 0 else "")
                   + (f"\\t({t1},{t2},\\bord{base_outline}\\blur0)" if t2 > t1 else "")
                   + "}")
            parts.append(tag + esc(txt))
        else:
            parts.append(f"{{\\rCap\\1c&H{inactive_color}&\\bord{base_outline}\\blur0}}{esc(txt)}")
        if i != len(block_words) - 1:
            parts.append(" ")
    return "".join(parts)

def build_ass(words, wpc=3, font="Montserrat", fs=72,
              bord=7, shad=0, margin_v=120, margin_lr=70,
              color_active="#FFB117", color_inactive="#FFFFFF", outline_color="#000000",
              uppercase=True, tail_hold=0.0,
              pop_in_ms=90, pop_out_ms=200, pop_outline_extra=3, pop_blur=0.8):
    header = ASS_HEADER_TPL.safe_substitute(
        font=font,
        fs=fs,
        inactive=rgb_to_ass_hex(color_inactive),
        outline=rgb_to_ass_hex(outline_color),
        bord=bord, shad=shad, ml=margin_lr, mr=margin_lr, mv=margin_v
    )
    lines = [header]

    n = len(words)
    i = 0
    while i < n:
        j = min(i + wpc, n)
        block = words[i:j]
        block_end = float(block[-1]["end"])

        for k, w in enumerate(block):
            start = float(w["start"])
            # hold highlight until next word begins; last holds until block end
            hold_end = float(block[k+1]["start"]) if k < len(block) - 1 else block_end + float(tail_hold)
            if hold_end <= start:
                hold_end = max(start + 0.01, float(w["end"]))

            dur_ms = int(round((hold_end - start) * 1000))
            # clamp pop windows within the event duration
            t_in  = min(pop_in_ms, max(0, dur_ms - 10))
            t_out = min(pop_out_ms, max(t_in, dur_ms))

            text = build_line_text(
                block, k, color_active, color_inactive,
                base_outline=bord,
                pop_in_ms=t_in, pop_out_ms=t_out,
                pop_outline_extra=pop_outline_extra, pop_blur=pop_blur,
                uppercase=uppercase
            )
            lines.append(f"Dialogue: 0,{to_ass_time(start)},{to_ass_time(hold_end)},Cap,,0,0,0,,{text}\n")
        i = j

    return "".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="temp/word_timestamps.json")
    ap.add_argument("--out", default="captions.ass")
    ap.add_argument("--words-per-cap", type=int, default=3)
    ap.add_argument("--font", default="Montserrat")
    ap.add_argument("--fontsize", type=int, default=92)
    ap.add_argument("--outline", type=int, default=7)
    ap.add_argument("--shadow", type=int, default=0)
    ap.add_argument("--margin-v", type=int, default=400)
    ap.add_argument("--margin-lr", type=int, default=70)
    ap.add_argument("--active", default="#FFB117")
    ap.add_argument("--inactive", default="#FFFFFF")
    ap.add_argument("--outline-color", default="#000000")
    ap.add_argument("--no-uppercase", action="store_true")
    ap.add_argument("--tail-hold", type=float, default=0.0)
    ap.add_argument("--pop-in-ms", type=int, default=90)
    ap.add_argument("--pop-out-ms", type=int, default=180)
    ap.add_argument("--pop-outline-extra", type=int, default=3)
    ap.add_argument("--pop-blur", type=float, default=0.8)

    args = ap.parse_args()
    words = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
    ass = build_ass(
        words,
        wpc=args.words_per_cap, font=args.font, fs=args.fontsize,
        bord=args.outline, shad=args.shadow, margin_v=args.margin_v, margin_lr=args.margin_lr,
        color_active=args.active, color_inactive=args.inactive, outline_color=args.outline_color,
        uppercase=not args.no_uppercase, tail_hold=args.tail_hold,
        pop_in_ms=args.pop_in_ms, pop_out_ms=args.pop_out_ms,
        pop_outline_extra=args.pop_outline_extra, pop_blur=args.pop_blur
    )
    pathlib.Path(args.out).write_text(ass, encoding="utf-8")
    print("Wrote", args.out)

if __name__ == "__main__":
    main()
