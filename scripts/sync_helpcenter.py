#!/usr/bin/env python3
"""
Sync Coohom Help Center articles from Kujiale API into knowledge/*.mdx.

Python port of CoohomHelpCenterAi HelpCenterSyncController.syncToMarkdown.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from html_to_markdown import HtmlToMarkdownUtil
from knowledge_common import (
    KNOWLEDGE_ROOT,
    build_file_base_name,
    locale_to_lang,
    refresh_docs_navigation,
    write_mdx,
)

HELP_CENTER_DOCS_URL = (
    "https://www.kujiale.com/helpcenter/api/visible/articles"
    "?hc_ns=coohom&page={page}&size={size}"
    "&updatedStartTime={start}&updatedEndTime={end}"
)


@dataclass
class SyncResult:
    output_dir: str = ""
    total: int = 0
    written: int = 0
    failed_count: int = 0
    written_files: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def fetch_help_center_docs(start_time: int, end_time: int, page_size: int = 100) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = HELP_CENTER_DOCS_URL.format(
            page=page, size=page_size, start=start_time, end=end_time
        )
        req = Request(url, headers={"User-Agent": "KnowledgeRepository-sync/1.0"})
        try:
            with urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"Help Center API request failed: {exc}") from exc

        if payload.get("c") not in (None, "0", 0):
            raise RuntimeError(
                f"Help Center API error: c={payload.get('c')} m={payload.get('m')}"
            )

        batch = (payload.get("d") or {}).get("data") or []
        docs.extend(batch)
        if not batch or len(batch) < page_size:
            break
        page += 1
    return docs


def pick_title(doc: dict[str, Any], slug: str) -> str:
    for key in ("title", "name"):
        value = doc.get(key)
        if value and str(value).strip():
            return str(value).strip()
    from knowledge_common import title_from_slug

    return title_from_slug(slug)


def sync_to_knowledge(
    start_time: int,
    end_time: int,
    only_publish: bool = True,
    update_nav: bool = True,
) -> SyncResult:
    html_util = HtmlToMarkdownUtil()
    result = SyncResult(output_dir=str(KNOWLEDGE_ROOT.resolve()))

    docs = fetch_help_center_docs(start_time, end_time)
    if only_publish:
        docs = [d for d in docs if d.get("status") == "PUBLISH"]

    result.total = len(docs)

    for doc in docs:
        article_id = str(doc.get("articleId") or "")
        name = str(doc.get("name") or "")
        try:
            html = doc.get("content") or ""
            markdown = html_util.convert_article_html(html)
            lang = locale_to_lang(doc.get("locale"))
            slug = build_file_base_name(article_id, name)
            title = pick_title(doc, slug)
            _, path, _ = write_mdx(lang, slug, title, markdown)
            target = KNOWLEDGE_ROOT / lang / f"{slug}.mdx"
            result.written_files.append(str(target.resolve()))
            result.written += 1
            print(f"[{lang}] {title} -> {path}")
        except Exception as exc:
            result.failed.append(f"{article_id}|{name}|{exc}")
            result.failed_count += 1
            print(f"FAILED {article_id}|{name}: {exc}", file=sys.stderr)

    if update_nav:
        refresh_docs_navigation()
        print("Updated docs.json navigation from knowledge/")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Help Center articles to knowledge/*.mdx (Mintlify)."
    )
    parser.add_argument("--start-time", type=int, help="updatedStartTime (epoch ms)")
    parser.add_argument("--end-time", type=int, help="updatedEndTime (epoch ms)")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Look back N days when --start-time omitted (default: 1)",
    )
    parser.add_argument(
        "--only-publish",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Only sync PUBLISH status (default: true)",
    )
    parser.add_argument(
        "--no-update-nav",
        action="store_true",
        help="Skip regenerating docs.json navigation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print SyncResult as JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    end_ms = args.end_time if args.end_time is not None else int(time.time() * 1000)
    if args.start_time is not None:
        start_ms = args.start_time
    else:
        days = max(args.days or 0, 0)
        start_dt = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc) - timedelta(
            days=days
        )
        start_ms = int(start_dt.timestamp() * 1000)

    print(
        f"Sync range: {start_ms} .. {end_ms} "
        f"({datetime.fromtimestamp(start_ms/1000, tz=timezone.utc).isoformat()} "
        f"→ {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).isoformat()})"
    )

    result = sync_to_knowledge(
        start_ms,
        end_ms,
        only_publish=args.only_publish,
        update_nav=not args.no_update_nav,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "outputDir": result.output_dir,
                    "total": result.total,
                    "written": result.written,
                    "failedCount": result.failed_count,
                    "writtenFiles": result.written_files,
                    "failed": result.failed,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(
            f"\nDone: total={result.total} written={result.written} "
            f"failed={result.failed_count} -> {result.output_dir}"
        )
        if result.failed:
            print("Failures:")
            for item in result.failed:
                print(f"  - {item}")

    return 1 if result.failed_count else 0


if __name__ == "__main__":
    sys.exit(main())
