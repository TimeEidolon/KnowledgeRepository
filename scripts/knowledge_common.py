"""Shared helpers for knowledge/*.mdx and docs.json generation."""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_ROOT = ROOT / "knowledge"

LANG_LABELS = {
    "en": "English",
    "zh": "简体中文",
    "ja": "日本語",
}

LOCALE_TO_LANG = {
    "en_us": "en",
    "zh_cn": "zh",
    "ja_jp": "ja",
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


def locale_to_lang(locale: str | None) -> str:
    if not locale or not locale.strip():
        return "en"
    key = safe_path_segment(locale)
    return LOCALE_TO_LANG.get(key, key.split("_")[0] if key else "en")


def safe_path_segment(raw: str) -> str:
    if not raw or not str(raw).strip():
        return "unknown"
    s = str(raw).strip()
    s = re.sub(r"[^\w\u4e00-\u9fff\u3040-\u30ff.-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s)
    s = re.sub(r"^_+|_+$", "", s)
    s = s.lower()
    return s if s else "unknown"


def build_file_base_name(article_id: str | None, name: str | None) -> str:
    aid = safe_path_segment(article_id or "")
    nm = safe_path_segment(name or "")
    if aid != "unknown" and nm != "unknown":
        return f"{aid}_{nm}"
    if aid != "unknown":
        return aid
    if nm != "unknown":
        return nm
    return f"unknown_{int(time.time() * 1000)}"


def title_from_slug(slug: str) -> str:
    name = slug.split("_", 1)[-1] if "_" in slug else slug
    name = name.replace("_", " ").strip()
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", name):
        return name
    return name[:1].upper() + name[1:] if name else slug


def categorize(lang: str, slug: str) -> str:
    if lang == "en":
        tail = slug.split("_", 1)[-1].lower() if "_" in slug else slug.lower()
        for prefix, group in EN_CATEGORY_RULES:
            if tail.startswith(prefix) or prefix.rstrip("_") in tail.split("_")[:3]:
                return group
        return "General"
    if lang == "zh":
        tail = slug.split("_", 1)[-1] if "_" in slug else slug
        for prefix, group in ZH_CATEGORY_RULES:
            if tail.startswith(prefix):
                return group
        return "其他"
    return JA_CATEGORY


def fix_angle_bracket_urls(text: str) -> str:
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
                out.append(f"{level} {title}" if title else line)
                i += 2
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def escape_mdx_curly_braces(text: str) -> str:
    """Escape `{`/`}` so MDX does not treat them as JSX expressions."""
    text = re.sub(r"(?<!\\)\{", r"\\{", text)
    text = re.sub(r"(?<!\\)\}", r"\\}", text)
    return text


def escape_mdx_operators(text: str) -> str:
    """Escape `<` patterns that MDX would parse as JSX."""
    text = text.replace("<=", "≤").replace(">=", "≥")
    text = re.sub(r"(?<!<)<(\d)", r"&lt;\1", text)
    text = re.sub(r"<([A-Z][^>\n]*)>", r"&lt;\1&gt;", text)
    return text


IMAGE_MD_RE = re.compile(r"!\[\]\((https?://[^)\s]+)\)")
VIDEO_MD_RE = re.compile(
    r"(?:🎥\s*)?\[Video URL\]\((https?://[^)]+)\)|"
    r"https?://(?:www\.)?youtube\.com/watch\?v=([\w-]{6,})|"
    r"https?://youtu\.be/([\w-]{6,})",
    re.IGNORECASE,
)
AGENT_VISIBILITY_RE = re.compile(
    r"\n*<Visibility for=\"agents\">.*?</Visibility>\s*",
    re.DOTALL,
)


def youtube_embed_html(url: str) -> str:
    match = VIDEO_MD_RE.search(url)
    video_id = None
    if match:
        video_id = match.group(2) or match.group(3)
    if not video_id and "youtube.com/embed/" in url:
        video_id = url.rsplit("/", 1)[-1].split("?", 1)[0]
    if video_id:
        return (
            f'<iframe width="100%" height="400" '
            f'src="https://www.youtube.com/embed/{video_id}" '
            f'title="Video" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'
        )
    return f"[Video]({url})"


def extract_intro_video(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "🎥" in stripped or "video" in stripped.lower() or "youtube" in stripped.lower():
            match = VIDEO_MD_RE.search(stripped)
            if match:
                url = match.group(1) or (
                    f"https://www.youtube.com/watch?v={match.group(2) or match.group(3)}"
                )
                return youtube_embed_html(url)
    return None


def extract_step_media_pairs(body: str) -> list[tuple[str, list[str]]]:
    """Map preceding text to image URLs in document order."""
    steps: list[tuple[str, list[str]]] = []
    buffer: list[str] = []

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<"):
            continue
        if stripped.startswith("## Assistant step guide"):
            break
        images = IMAGE_MD_RE.findall(stripped)
        if images:
            text = " ".join(buffer).strip()
            text = re.sub(r"^#+\s*", "", text).strip()
            if not text:
                text = f"Step {len(steps) + 1}"
            steps.append((text, images))
            buffer = []
            continue
        if stripped.startswith("#"):
            buffer = [stripped.lstrip("#").strip()]
        elif not stripped.startswith("🎥"):
            buffer.append(stripped)

    return steps


def build_agent_media_block(body: str) -> str:
    """Hidden block indexed for AI assistant with step text + image URLs."""
    clean = AGENT_VISIBILITY_RE.sub("\n", body).strip()
    steps = extract_step_media_pairs(clean)
    intro_video = extract_intro_video(clean)
    if not steps and not intro_video:
        return ""

    parts = [
        '<Visibility for="agents">',
        "",
        "## Assistant step guide",
        "",
        "Include every image below in your answer. For each step, output the step line, "
        "then `![](IMAGE_URL)` on the next line using the exact URL.",
        "",
    ]
    if intro_video:
        parts.extend([intro_video, ""])
    for index, (text, urls) in enumerate(steps, start=1):
        parts.append(f"{index}. {text}")
        for url in urls:
            parts.append(f"![]({url})")
        parts.append("")
    parts.append("</Visibility>")
    return "\n".join(parts)


def attach_agent_media_block(body: str) -> str:
    block = build_agent_media_block(body)
    if not block:
        return body
    base = AGENT_VISIBILITY_RE.sub("\n", body).rstrip()
    return f"{base}\n\n{block}\n"


def prepare_mdx_body(markdown: str) -> str:
    body = convert_underline_headings(markdown)
    body = fix_angle_bracket_urls(body)
    body = escape_mdx_operators(body)
    body = escape_mdx_curly_braces(body)
    body = body.replace(r"\[Video URL\]", "[Video URL]")
    return body.strip()


def description_from_body(body: str, fallback: str) -> str:
    desc = body.strip().split("\n")[0][:160]
    desc = re.sub(r"^[#>*\s]+", "", desc)
    desc = desc.replace("\\", "").strip()
    return desc or fallback


def write_mdx(
    lang: str,
    slug: str,
    title: str,
    body: str,
) -> tuple[str, str, str]:
    """Write knowledge/{lang}/{slug}.mdx. Returns (category, page_path, title)."""
    prepared = attach_agent_media_block(prepare_mdx_body(body))
    desc = description_from_body(prepared, title)
    dest_dir = KNOWLEDGE_ROOT / lang
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{slug}.mdx"
    frontmatter = (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"description: {json.dumps(desc[:200], ensure_ascii=False)}\n"
        "---\n\n"
    )
    dest.write_text(frontmatter + prepared + "\n", encoding="utf-8")
    return categorize(lang, slug), f"knowledge/{lang}/{slug}", title


def parse_mdx_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\s*\n.*?title:\s*(.+?)\s*\n", text, re.DOTALL)
    if not match:
        return title_from_slug(path.stem)
    raw = match.group(1).strip()
    if raw.startswith('"') or raw.startswith("'"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip("\"'")
    return raw


def write_index_pages() -> None:
    titles = {
        "en": ("Coohom Help Center", "Browse Coohom product guides and how-to articles."),
        "zh": ("Coohom 帮助中心", "浏览 Coohom 产品使用指南与操作说明。"),
        "ja": ("Coohom ヘルプセンター", "Coohom の製品ガイドと操作方法をご覧ください。"),
    }
    for code, label in LANG_LABELS.items():
        t, d = titles[code]
        dest = KNOWLEDGE_ROOT / code / "index.mdx"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            f"---\ntitle: {json.dumps(t, ensure_ascii=False)}\n"
            f"description: {json.dumps(d, ensure_ascii=False)}\n---\n\n"
            f"Welcome to the Coohom knowledge base ({label}). "
            "Use the sidebar to find guides by topic.\n",
            encoding="utf-8",
        )


def collect_entries_from_disk() -> dict[str, list[tuple[str, str, str]]]:
    entries: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for lang in LANG_LABELS:
        lang_dir = KNOWLEDGE_ROOT / lang
        if not lang_dir.exists():
            continue
        for mdx in sorted(lang_dir.glob("*.mdx")):
            if mdx.stem == "index":
                continue
            slug = mdx.stem
            title = parse_mdx_title(mdx)
            cat = categorize(lang, slug)
            entries[lang].append((cat, f"knowledge/{lang}/{slug}", title))
    return entries


def build_navigation(entries: dict[str, list[tuple[str, str, str]]]) -> list[dict]:
    languages = []
    for code, label in LANG_LABELS.items():
        items = entries.get(code, [])
        by_cat: dict[str, list[str]] = defaultdict(list)
        for cat, path, _ in sorted(items, key=lambda x: (x[0], x[1])):
            by_cat[cat].append(path)
        groups = [{"group": cat, "pages": by_cat[cat]} for cat in sorted(by_cat)]
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
        json.dumps(docs, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def refresh_docs_navigation() -> None:
    write_index_pages()
    entries = collect_entries_from_disk()
    nav = build_navigation(entries)
    nav_path = ROOT / "scripts" / "navigation-languages.json"
    nav_path.write_text(json.dumps(nav, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_docs_json(nav)
