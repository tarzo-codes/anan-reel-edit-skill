"""User rule (8-11-2026 pass 3): every English word he SAYS is written in English (Latin) inside the Bangla captions.
Longest matches first. Applied to the caption strings of plan_r1..r6.py."""
import re
import sys

T = [
    ("ফান্ডামেন্টাল অ্যানালাইসিস", "fundamental analysis"), ("টেকনিক্যাল অ্যানালাইসিস", "technical analysis"),
    ("মানি ম্যানেজমেন্ট", "money management"), ("প্রাইস অ্যাকশন", "price action"), ("মোরাল অফ দ্য স্টোরি", "moral of the story"),
    ("টেলিগ্রাম চ্যানেলের", "Telegram channel-এর"), ("টেলিগ্রাম চ্যানেলে", "Telegram channel-এ"), ("টেলিগ্রামে", "Telegram-এ"),
    ("বিটকয়েনের মার্কেট", "Bitcoin-এর market"), ("ফাইন্যান্সিয়াল মার্কেট", "financial market"),
    ("ট্রেডিং চার্ট", "trading chart"), ("ট্রেডিংয়ে", "trading-এ"), ("ট্রেডিং", "trading"),
    ("চার্টটা", "chart-টা"), ("চার্টের", "chart-এর"), ("চার্ট", "chart"), ("ক্যান্ডেলগুলা", "candle-গুলা"), ("প্যাটার্ন", "pattern"),
    ("টিম মেম্বার", "team member"), ("সিগন্যাল", "signal"), ("কমেন্ট", "comment"), ("লিংক বায়োতে", "link bio-তে"),
    ("লাইফের", "life-এর"), ("লাইফে", "life-এ"), ("স্টপ লস", "stop loss"), ("সাইকোলজি", "psychology"), ("কন্ট্রোল", "control"),
    ("ইম্পরট্যান্ট", "important"), ("স্ট্র্যাটেজি", "strategy"), ("ভলিউম", "volume"), ("কম্বিনেশন", "combination"),
    ("চায়না ট্যুরে", "China tour-এ"), ("চায়নায়", "China-তে"), ("চায়না", "China"), ("মালয়েশিয়া", "Malaysia"), ("মালদ্বীপ", "Maldives"),
    ("সাউথ পার্ট কভার", "South part cover"), ("ডিগ্রি", "degree"), ("লিসেন", "Listen"), ("ব্রো", "bro"), ("আনসার", "answer"),
    ("সিম্পল", "simple"), ("আইডিয়া", "idea"), ("ব্যাকগ্রাউন্ডে", "background-এ"), ("গ্যারান্টি", "guarantee"), ("প্রবলেম", "problem"),
    ("ফিল করো", "feel করো"), ("ফার্স্ট", "first"), ("মাস্টার", "master"), ("অ্যারাউন্ড", "around"), ("গ্লোবালি", "globally"),
    ("এক্সিডেন্টে", "accident-এ"), ("লাকি", "lucky"), ("টাইম", "time"), ("ফ্যামিলির", "family-র"), ("জয়েন", "join"), ("রুলস", "rules"),
    ("লিংক", "link"), ("বায়োতে", "bio-তে"), ("ট্যুরে", "tour-এ"), ("ক্যান্ডেল", "candle"), ("ইজিলি", "easily"), ("ইজি", "easy"), ("জাস্ট", "just"), ("ইনকাম", "income"), ("মার্কেট", "market"),
    ("সো,", "So,"), ("বাট ", "but "), ("বাট", "but"),
]


def convert(s):
    for a, b in T:
        s = s.replace(a, b)
    return s


if __name__ == "__main__":
    for p in sys.argv[1:]:
        src = open(p, encoding="utf-8").read()
        # only string literals that contain Bangla (captions / comment text), never code
        new = re.sub(r'"([^"\n]*[ঀ-৿][^"\n]*)"', lambda m: '"' + convert(m.group(1)) + '"', src)
        if new != src:
            open(p, "w", encoding="utf-8").write(new)
        print(p, "changed" if new != src else "same")
