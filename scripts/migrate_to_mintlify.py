#!/usr/bin/env python3
"""Migrate markdown/ knowledge articles to knowledge/*.mdx and emit navigation JSON."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_ROOT = ROOT / "markdown"
KNOWLEDGE_ROOT = ROOT / "knowledge"

LANG_DIRS = {
    "en_us": ("en", "English"),
    "zh_cn": ("zh", "简体中文"),
    "ja_jp": ("ja", "日本語"),
}

EN_CATEGORY_RULES: list[tuple[str, str]] = [
    ("ceiling_design", "Ceiling design"),
    ("wall_design", "Wall design"),
    ("render_", "Rendering"),
    ("kitchen", "Kitchen & closet"),
    ("closet_design", "Kitchen & closet"),
    ("floor_plan", "Floor plan"),
    ("model_material", "Models & materials"),
    ("3d_models", "Models & materials"),
    ("3ds_max", "Models & materials"),
    ("upload_textures", "Models & materials"),
    ("material_component", "Models & materials"),
    ("coohom_", "Account & billing"),
    ("subscription", "Account & billing"),
    ("how_to_", "How-to guides"),
    ("360_walkthrough", "360 walkthrough"),
    ("march_2026", "Product updates"),
    ("april_2026", "Product updates"),
    ("snap_shot", "Rendering"),
    ("horizontal_rotation", "Rendering"),
    ("generate_a_futuristic", "Rendering"),
    ("how_many_3d", "Models & materials"),
    ("how_to_share", "360 walkthrough"),
]

ZH_CATEGORY_RULES: list[tuple[str, str]] = [
    ("3d模型", "模型与素材"),
    ("3ds_max", "模型与素材"),
    ("模型素材", "模型与素材"),
    ("coohom_3ds", "模型与素材"),
    ("coohom企业", "账户与积分"),
    ("coohom个人", "账户与积分"),
    ("橱柜设计", "定制设计"),
    ("全屋定制", "定制设计"),
    ("全屋设计", "定制设计"),
    ("户型工具", "户型工具"),
    ("elite团队", "团队空间"),
    ("渲染_", "渲染"),
    ("吊顶设计", "硬装设计"),
    ("背景墙设计", "硬装设计"),
]

JA_CATEGORY = "部品・モデル"


def slug_from_path(path: Path) -> str:
    return path.stem


def title_from_slug(slug: str) -> str:
    name = slug.split("_", 1)[-1] if "_" in slug else slug
    name = name.replace("_", " ").strip()
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", name):
        return name
    return name[:1].upper() + name[1:] if name else slug


def categorize_en(slug: str) -> str:
    tail = slug.split("_", 1)[-1].lower() if "_" in slug else slug.lower()
    for prefix, group in EN_CATEGORY_RULES:
        if tail.startswith(prefix) or prefix.rstrip("_") in tail.split("_")[:3]:
            return group
    return "General"


def categorize_zh(slug: str) -> str:
    tail = slug.split("_", 1)[-1] if "_" in slug else slug
    for prefix, group in ZH_CATEGORY_RULES:
        if tail.startswith(prefix):
            return group
    return "其他"


def fix_angle_bracket_urls(text: str) -> str:
    """Convert <https://...> autolinks to MDX-safe markdown links."""
    return re.sub(
        r"<\s*(https?://[^>\s]+)\s*>",
        lambda m: f"[{m.group(1)}]({m.group(1)})",
        text,
    )


def convert_underline_headings(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and set(nxt) <= {"=", "-"} and len(nxt) >= 3:
                level = "##" if nxt[0] == "=" else "###"
                title = line.strip()
                if title:
                    out.append(f"{level} {title}")
                else:
                    out.append(line)
                i += 2
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def migrate_file(src: Path, lang_code: str) -> tuple[str, str, str]:
    slug = slug_from_path(src)
    title = title_from_slug(slug)
    body = src.read_text(encoding="utf-8")
    body = convert_underline_headings(body)
    body = fix_angle_bracket_urls(body)
    body = body.replace(r"\[Video URL\]", "[Video URL]")

    desc = body.strip().split("\n")[0][:160]
    desc = re.sub(r"^[#>*\s]+", "", desc)
    desc = desc.replace("\\", "").strip() or title

    if lang_code == "en":
        category = categorize_en(slug)
    elif lang_code == "zh":
        category = categorize_zh(slug)
    else:
        category = JA_CATEGORY

    dest_dir = KNOWLEDGE_ROOT / lang_code
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{slug}.mdx"

    frontmatter = (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"description: {json.dumps(desc[:200], ensure_ascii=False)}\n"
        "---\n\n"
    )
    dest.write_text(frontmatter + body.strip() + "\n", encoding="utf-8")
    page_path = f"knowledge/{lang_code}/{slug}"
    return category, page_path, title


def build_navigation(entries: dict[str, list[tuple[str, str]]]) -> list[dict]:
    """entries: lang_code -> list of (category, page_path) sorted."""
    languages = []
    for folder, (code, label) in LANG_DIRS.items():
        items = entries.get(code, [])
        by_cat: dict[str, list[str]] = defaultdict(list)
        for cat, path, _ in sorted(items, key=lambda x: (x[0], x[1])):
            by_cat[cat].append(path)

        groups = []
        for cat in sorted(by_cat.keys()):
            groups.append({"group": cat, "pages": by_cat[cat]})

        languages.append(
            {
                "language": code,
                "label": label,
                "tabs": [
                    {
                        "tab": "Help Center",
                        "groups": [
                            {"group": "Overview", "pages": [f"knowledge/{code}/index"]},
                            *groups,
                        ],
                    }
                ],
            }
        )
    return languages


def write_index_pages():
    for code, label in [(v[0], v[1]) for v in LANG_DIRS.values()]:
        dest = KNOWLEDGE_ROOT / code / "index.mdx"
        titles = {
            "en": ("Coohom Help Center", "Browse Coohom product guides and how-to articles."),
            "zh": ("Coohom 帮助中心", "浏览 Coohom 产品使用指南与操作说明。"),
            "ja": ("Coohom ヘルプセンター", "Coohom の製品ガイドと操作方法をご覧ください。"),
        }
        t, d = titles[code]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            f"---\ntitle: \"{t}\"\ndescription: \"{d}\"\n---\n\n"
            f"Welcome to the Coohom knowledge base ({label}). "
            "Use the sidebar to find guides by topic.\n",
            encoding="utf-8",
        )


def write_docs_json(nav: list[dict]) -> None:
    docs = {
        "$schema": "https://mintlify.com/docs.json",
        "theme": "mint",
        "name": "Coohom Help Center",
        "colors": {"primary": "#2563EB", "light": "#3B82F6", "dark": "#1D4ED8"},
        "favicon": "/favicon.svg",
        "navigation": {"languages": nav},
        "logo": {"light": "/logo/light.svg", "dark": "/logo/dark.svg"},
        "navbar": {
            "links": [{"label": "Coohom", "href": "https://www.coohom.com"}],
            "primary": {
                "type": "button",
                "label": "Go to Coohom",
                "href": "https://www.coohom.com",
            },
        },
        "contextual": {
            "options": [
                "copy",
                "view",
                "chatgpt",
                "claude",
                "perplexity",
                "mcp",
                "cursor",
                "vscode",
            ]
        },
        "seo": {"indexing": "all"},
        "footer": {"socials": {"github": "https://github.com/mintlify"}},
    }
    (ROOT / "docs.json").write_text(
        json.dumps(docs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    entries: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for folder, (code, _) in LANG_DIRS.items():
        src_dir = MARKDOWN_ROOT / folder
        if not src_dir.exists():
            continue
        for src in sorted(src_dir.glob("*.md")):
            cat, path, title = migrate_file(src, code)
            entries[code].append((cat, path, title))
            print(f"Migrated [{code}] {title}")

    write_index_pages()

    nav = build_navigation(entries)
    nav_path = ROOT / "scripts" / "navigation-languages.json"
    nav_path.write_text(json.dumps(nav, ensure_ascii=False, indent=2), encoding="utf-8")
    write_docs_json(nav)
    print(f"\nWrote {nav_path} and docs.json")
    print(f"Total pages: {sum(len(v) for v in entries.values())} + index per language")


if __name__ == "__main__":
    main()
