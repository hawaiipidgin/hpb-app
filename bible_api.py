from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ allow your HTML page
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load dataset safely
bible_df = pd.read_csv("pidgin_bible_full.csv")
# ✅ normalize dataset ONCE
bible_df["Book"] = bible_df["Book"].astype(str).str.strip().str.lower()
bible_df["Chapter"] = bible_df["Chapter"].astype(int)
bible_df["Verse"] = bible_df["Verse"].astype(int)
print(bible_df["Book"].unique()[:20])
# ✅ Parse reference (simple & reliable)
def parse_reference(ref):
    ref = ref.strip()

    if ":" not in ref:
        return None

    parts = ref.split()

    if len(parts) < 2:
        return None

    book = " ".join(parts[:-1])
    chap, verse = parts[-1].split(":")

    return book, int(chap), int(verse)
    
# ✅ full + short aliases
book_aliases = {
    # ✅ Old Testament
    "gen": "genesis", "ge": "genesis",
    "exo": "exodus", "ex": "exodus",
    "lev": "leviticus",
    "num": "numbers",
    "deut": "deuteronomy", "deu": "deuteronomy",
    "jos": "joshua",
    "jdg": "judges",
    "rut": "ruth",
    "1sa": "1 samuel", "2sa": "2 samuel",
    "1ki": "1 kings", "2ki": "2 kings",
    "1ch": "1 chronicles", "2ch": "2 chronicles",
    "ezr": "ezra",
    "neh": "nehemiah",
    "est": "esther",
    "job": "job",
    "ps": "psalms", "psalm": "psalms",
    "pro": "proverbs",
    "ecc": "ecclesiastes",
    "song": "song of solomon", "sos": "song of solomon",
    "isa": "isaiah",
    "jer": "jeremiah",
    "lam": "lamentations",
    "ezk": "ezekiel",
    "dan": "daniel",
    "hos": "hosea",
    "joel": "joel",
    "amos": "amos",
    "oba": "obadiah",
    "jon": "jonah",
    "mic": "micah",
    "nah": "nahum",
    "hab": "habakkuk",
    "zep": "zephaniah",
    "hag": "haggai",
    "zec": "zechariah",
    "mal": "malachi",

    # ✅ New Testament
    "mt": "matthew", "mat": "matthew",
    "mk": "mark", "mrk": "mark",
    "lk": "luke",
    "jn": "john",
    "acts": "acts",
    "rom": "romans",
    "1cor": "1 corinthians", "2cor": "2 corinthians",
    "gal": "galatians",
    "eph": "ephesians",
    "php": "philippians", "phil": "philippians",
    "col": "colossians",
    "1th": "1 thessalonians", "2th": "2 thessalonians",
    "1tim": "1 timothy", "2tim": "2 timothy",
    "tit": "titus",
    "phm": "philemon",
    "heb": "hebrews",
    "jas": "james",
    "1pet": "1 peter", "2pet": "2 peter",
    "1jn": "1 john", "2jn": "2 john", "3jn": "3 john",
    "jud": "jude",
    "rev": "revelation"
}


# ✅ CLEAN + SAFE LOOKUP
def get_verse(book, chapter, verse):
    try:
        book = book.strip().lower()

        if book in book_aliases:
            book = book_aliases[book]

        result = bible_df[
            (bible_df["Book"] == book) &
            (bible_df["Chapter"] == int(chapter)) &
            (bible_df["Verse"] == int(verse))
        ]

        if not result.empty:
            return result.iloc[0]["Text"]

        return "No can find dat verse."

    except Exception as e:
        print("ERROR:", e)
        return "Error pulling verse."

# ✅ API ROUTE

@app.get("/verse")
def get_scripture(reference: str):
    try:
        parts = reference.split()

        book = parts[0]
        chapter_part = parts[1]

        # ✅ normalize book
        book_clean = book.strip().lower()
        if book_clean in book_aliases:
            book_clean = book_aliases[book_clean]

        # ✅ check if range
        if "-" in chapter_part:
            chapter, verses_range = chapter_part.split(":")
            start, end = verses_range.split("-")

            start = int(start)
            end = int(end)

            verses_list = []

            for v in range(start, end + 1):
                text = get_verse(book_clean, chapter, v)

                verses_list.append({
                    "verse": v,
                    "text": text
                })

            return {
                "reference": reference,
                "book": book_clean.capitalize(),
                "chapter": int(chapter),
                "verses": verses_list
            }

        else:
            # ✅ single verse
            chapter, verse = chapter_part.split(":")

            text = get_verse(book_clean, chapter, verse)

            return {
                "reference": reference,
                "book": book_clean.capitalize(),
                "chapter": int(chapter),
                "verses": [
                    {
                        "verse": int(verse),
                        "text": text
                    }
                ]
            }

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Invalid reference"}

    parsed = parse_reference(ref)

    if not parsed:
        return {"error": "Invalid reference"}

    book, chapter, verse = parsed

    text = get_verse(book, chapter, verse)

    return {
        "reference": ref,
        "book": book,
        "chapter": chapter,
        "verses": [
            {
                "verse": verse,
                "text": text
            }
        ]
    }
@app.get("/search")
def search_verses(q: str):
    try:
        import re

        query = q.strip()
        words = query.lower().split()

        # ✅ filter: must contain ALL words
        results = bible_df.copy()

        for word in words:
            results = results[
                results["Text"].str.lower().str.contains(word, na=False)
            ]

        results = results.head(20)

        verses_list = []

        for _, row in results.iterrows():
            text = row["Text"]

            # ✅ highlight ALL words
            for word in words:
                text = re.sub(
                    f"({word})",
                    r"**\1**",
                    text,
                    flags=re.IGNORECASE
                )

            verses_list.append({
                "book": row["Book"].capitalize(),
                "chapter": int(row["Chapter"]),
                "verse": int(row["Verse"]),
                "text": text
            })

        return {
            "query": q,
            "words": words,
            "count": len(verses_list),
            "results": verses_list
        }

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Search failed"}