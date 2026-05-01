from pathlib import Path
from collections import Counter

AUTHORS_DIR = Path(__file__).resolve().parent / "authors"

SPECIAL_AUTHOR_NAMES = {
    "lawrence-dh": "D. H. Lawrence",
    "wodehouse-pg": "P. G. Wodehouse",
    "pliny-the-elder": "Pliny the Elder",
}

LOWERCASE_NAME_WORDS = {"the", "of", "and", "de", "da", "di", "du", "van", "von"}


def format_name_token(token):
    if len(token) == 1:
        return token.upper() + "."
    if token in LOWERCASE_NAME_WORDS:
        return token
    return token.capitalize()


def author_from_slug(slug):
    if slug in SPECIAL_AUTHOR_NAMES:
        return SPECIAL_AUTHOR_NAMES[slug]

    parts = slug.split("-")
    if len(parts) == 1:
        return format_name_token(parts[0])

    surname = format_name_token(parts[0])
    given_names = [format_name_token(part) for part in parts[1:]]
    return " ".join(given_names + [surname])


def read_front_matter(path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}

    try:
        end = text.index("\n---", 3)
    except ValueError:
        return {}

    front_matter = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        front_matter[key.strip()] = value

    return front_matter


def most_common_chapter_value(book_folder, key):
    values = Counter()
    for chapter_path in book_folder.glob("chapter-*.md"):
        value = read_front_matter(chapter_path).get(key)
        if value:
            values[value] += 1

    if not values:
        return None

    return values.most_common(1)[0][0]


def book_title_from_slug(slug):
    return " ".join(format_name_token(part) for part in slug.split("-"))


def yaml_quote(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def create_indexes():
    for author_folder in AUTHORS_DIR.iterdir():
        if not author_folder.is_dir():
            continue

        author_name = author_from_slug(author_folder.name)

        # 1. Create Author Index (e.g., Jane Austen landing page)
        author_index_path = author_folder / "index.md"
        if not author_index_path.exists():
            with open(author_index_path, "w", encoding="utf-8") as f:
                f.write(
                    "---\n"
                    "layout: author_index\n"
                    f"title: {yaml_quote(author_name)}\n"
                    f"author_name: {yaml_quote(author_name)}\n"
                    "---\n"
                )

        # 2. Create Book Indexes (e.g., Emma landing page)
        for book_folder in author_folder.iterdir():
            if not book_folder.is_dir():
                continue

            book_title = most_common_chapter_value(book_folder, "book") or book_title_from_slug(book_folder.name)
            book_author = most_common_chapter_value(book_folder, "author") or author_name

            book_index_path = book_folder / "index.md"
            if not book_index_path.exists():
                with open(book_index_path, "w", encoding="utf-8") as f:
                    f.write(
                        "---\n"
                        "layout: book_index\n"
                        f"title: {yaml_quote(book_title)}\n"
                        f"book_title: {yaml_quote(book_title)}\n"
                        f"author: {yaml_quote(book_author)}\n"
                        "---\n"
                    )

    print("Successfully seeded all index files!")


if __name__ == "__main__":
    create_indexes()
