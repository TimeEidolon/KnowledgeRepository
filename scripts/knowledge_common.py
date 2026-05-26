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
VISIBLE_GUIDE_RE = re.compile(
    r"\n*## Steps with screenshots\n.*?(?=\n# [^#]|\n<Visibility|\Z)",
    re.DOTALL,
)
NUMBERED_STEP_RE = re.compile(r"^(\d+)\.\s+(.+)$")


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


def extract_intro_video_url(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "🎥" in stripped or "video" in stripped.lower() or "youtube" in stripped.lower():
            match = VIDEO_MD_RE.search(stripped)
            if match:
                return match.group(1) or (
                    f"https://www.youtube.com/watch?v={match.group(2) or match.group(3)}"
                )
    embed = re.search(r"youtube\.com/embed/([\w-]{6,})", body)
    if embed:
        return f"https://www.youtube.com/watch?v={embed.group(1)}"
    return None


def extract_intro_video(body: str) -> str | None:
    url = extract_intro_video_url(body)
    return youtube_embed_html(url) if url else None


def steps_with_media(
    steps: list[tuple[int, str, list[str]]],
) -> list[tuple[int, str, list[str]]]:
    """Keep only steps that have screenshots; renumber sequentially."""
    with_images = [(text, urls) for _, text, urls in steps if urls]
    return [(index, text, urls) for index, (text, urls) in enumerate(with_images, start=1)]


def _strip_generated_sections(body: str) -> str:
    body = AGENT_VISIBILITY_RE.sub("\n", body)
    body = VISIBLE_GUIDE_RE.sub("\n", body)
    return body.strip()


def extract_numbered_steps_with_images(body: str) -> list[tuple[int, str, list[str]]]:
    """Parse `1.` numbered steps and attach following image URLs."""
    clean = _strip_generated_sections(body)
    steps: list[tuple[int, str, list[str]]] = []
    current_num: int | None = None
    current_text: list[str] = []
    pending_images: list[str] = []
    buffer: list[str] = []

    def flush_step() -> None:
        nonlocal current_num, current_text, pending_images
        if current_num is None:
            pending_images = []
            return
        text = " ".join(current_text).strip()
        text = re.sub(r"\s+", " ", text)
        steps.append(
            (
                current_num,
                text or f"Step {current_num}",
                list(pending_images),
            )
        )
        current_num = None
        current_text = []
        pending_images = []

    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<"):
            continue
        if stripped.startswith("## Assistant step guide") or stripped.startswith(
            "## Steps with screenshots"
        ):
            break

        if re.match(r"^#{1,2}\s+\S", stripped) and not stripped.startswith("###"):
            flush_step()
            current_num = None
            current_text = []
            pending_images = []
            buffer = [stripped.lstrip("#").strip()]
            continue

        numbered = NUMBERED_STEP_RE.match(stripped)
        if numbered:
            flush_step()
            current_num = int(numbered.group(1))
            current_text = [numbered.group(2).strip()]
            buffer = []
            continue

        images = IMAGE_MD_RE.findall(stripped)
        if images:
            if current_num is not None:
                pending_images.extend(images)
            else:
                text = " ".join(buffer).strip() or f"Screenshot {len(steps) + 1}"
                steps.append((len(steps) + 1, text, images))
                buffer = []
            continue

        if current_num is not None and not stripped.startswith("#"):
            if not stripped.startswith("🎥"):
                current_text.append(stripped)
            continue

        buffer.append(stripped)
        if len(buffer) > 6:
            buffer = buffer[-6:]

    flush_step()

    if steps:
        return steps

    # Fallback: heading/buffer pairing for pages without numbered lists.
    fallback: list[tuple[int, str, list[str]]] = []
    buffer: list[str] = []
    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<"):
            continue
        images = IMAGE_MD_RE.findall(stripped)
        if images:
            text = " ".join(buffer).strip() or f"Step {len(fallback) + 1}"
            fallback.append((len(fallback) + 1, text, images))
            buffer = []
            continue
        if stripped.startswith("#"):
            buffer = [stripped.lstrip("#").strip()]
        elif not stripped.startswith("🎥"):
            buffer.append(stripped)
    return fallback


def extract_step_media_pairs(body: str) -> list[tuple[str, list[str]]]:
    return [(text, urls) for _, text, urls in extract_numbered_steps_with_images(body)]


def build_visible_step_guide(body: str) -> str:
    """Visible section with steps + images for humans and AI indexing."""
    steps = steps_with_media(extract_numbered_steps_with_images(body))
    if not steps:
        return ""

    video_url = extract_intro_video_url(_strip_generated_sections(body))
    lines = [
        "## Steps with screenshots",
        "",
        "Each step includes plain MEDIA_* URLs (for AI tools) plus rendered images.",
        "",
    ]
    if video_url:
        lines.extend(
            [
                f"MEDIA_VIDEO: {video_url}",
                "",
                extract_intro_video(body) or "",
                "",
            ]
        )
    for num, text, urls in steps:
        lines.append(f"### Step {num}")
        lines.append(text)
        lines.append("")
        for index, url in enumerate(urls, start=1):
            suffix = "" if len(urls) == 1 else f"_{index}"
            lines.append(f"MEDIA_STEP_{num}_IMAGE{suffix}: {url}")
            lines.append(f"![]({url})")
            lines.append(
                f'<img src="{url}" alt="Step {num}" style="max-width:100%;height:auto;" />'
            )
            lines.append("")
    return "\n".join(lines).strip()


def build_agent_media_block(body: str) -> str:
    """Hidden block indexed for AI assistant with plain-text media URLs."""
    clean = _strip_generated_sections(body)
    steps = steps_with_media(extract_numbered_steps_with_images(clean))
    video_url = extract_intro_video_url(clean)
    if not steps and not video_url:
        return ""

    parts = [
        '<Visibility for="agents">',
        "",
        "## Assistant step guide",
        "",
        "Mintlify assistant tools may strip markdown images. Always use the plain",
        "MEDIA_* lines below (they contain full https:// URLs).",
        "",
        "For each MEDIA_STEP_N_TEXT, output the step, then embed every matching",
        "MEDIA_STEP_N_IMAGE URL using:",
        '`<img src="URL" alt="Step" style="max-width:100%;height:auto;" />`',
        "",
    ]
    if video_url:
        parts.append(f"MEDIA_VIDEO: {video_url}")
        embed = youtube_embed_html(video_url)
        if embed:
            parts.append(embed)
        parts.append("")
    for num, text, urls in steps:
        parts.append(f"MEDIA_STEP_{num}_TEXT: {text}")
        for index, url in enumerate(urls, start=1):
            suffix = "" if len(urls) == 1 else f"_{index}"
            parts.append(f"MEDIA_STEP_{num}_IMAGE{suffix}: {url}")
        parts.append("")
    parts.append("</Visibility>")
    return "\n".join(parts)


def _insert_visible_guide(body: str, guide: str) -> str:
    if not guide:
        return body
    lines = body.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if "🎥" in stripped or "youtube.com" in stripped.lower():
            insert_at = index + 1
            break
        if stripped.startswith("# For Users") or stripped.startswith("# Entrance"):
            insert_at = index
            break
    if insert_at == 0:
        for index, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("---"):
                insert_at = index + 1
                break
    new_lines = lines[:insert_at] + ["", guide, ""] + lines[insert_at:]
    return "\n".join(new_lines)


def enrich_article_body(body: str) -> str:
    base = _strip_generated_sections(body)
    guide = build_visible_step_guide(base)
    if guide:
        base = _insert_visible_guide(base, guide)
    block = build_agent_media_block(base)
    if block:
        base = f"{base.rstrip()}\n\n{block}\n"
    return base


def attach_agent_media_block(body: str) -> str:
    return enrich_article_body(body)


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
    prepared = enrich_article_body(prepare_mdx_body(body))
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
