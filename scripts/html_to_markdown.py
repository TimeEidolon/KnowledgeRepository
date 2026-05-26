"""Port of CoohomHelpCenterAi HtmlToMarkdownUtil (HTML → Markdown)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md


class HtmlToMarkdownUtil:
    def html_to_markdown(self, html: str) -> str:
        if not html or not html.strip():
            return ""
        try:
            return md(html, heading_style="ATX", strip=["script", "style"]).strip()
        except Exception as exc:
            raise RuntimeError(f"HTML 转 Markdown 失败: {exc}") from exc

    def preprocess_iframes(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "youtube.com/embed/" in src:
                video_id = src.rsplit("/", 1)[-1]
                if "?" in video_id:
                    video_id = video_id.split("?", 1)[0]
                replacement = f"🎥 [Video URL](https://www.youtube.com/watch?v={video_id})"
            else:
                replacement = f"🎥 [Video URL]({src})"
            p = soup.new_tag("p")
            p.string = replacement
            iframe.replace_with(p)
        body = soup.body
        return body.decode_contents() if body else str(soup)

    def preprocess_image_links(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.select("a:has(img)"):
            img = link.find("img")
            if img is not None:
                if img.has_attr("data-group"):
                    del img["data-group"]
                link.replace_with(img)
        for img in soup.find_all("img"):
            if img.has_attr("title"):
                del img["title"]
        body = soup.body
        return body.decode_contents() if body else str(soup)

    def convert_article_html(self, html: str) -> str:
        processed = self.preprocess_image_links(self.preprocess_iframes(html))
        return self.html_to_markdown(processed)
