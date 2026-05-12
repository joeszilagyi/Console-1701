from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from console1701.news.normalize import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    bounded_text,
    normalize_timestamp,
    normalize_url,
)


class NewsIngestError(RuntimeError):
    """Base error for fixture ingest failures."""


class PayloadTooLargeError(NewsIngestError):
    """Raised when a local fixture exceeds the configured size cap."""


class UnsupportedSourceError(NewsIngestError):
    """Raised when a source is outside the local fixture-only phase."""


class NewsParserError(NewsIngestError):
    """Raised when a source fixture cannot be parsed."""


def resolve_file_url(url: str, *, config_dir: Path) -> Path:
    if not url.startswith("file://"):
        raise UnsupportedSourceError("Only file:// sources are allowed during fixture ingest.")
    raw_path = url[len("file://") :]
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (config_dir / path).resolve()
    return path


def load_fixture_text(
    source: dict[str, Any],
    *,
    config_dir: Path,
    max_bytes: int,
) -> tuple[str, Path]:
    path = resolve_file_url(str(source.get("url") or ""), config_dir=config_dir)
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise NewsIngestError(f"Fixture file not found: {path}") from exc
    if size > max_bytes:
        raise PayloadTooLargeError(
            f"Fixture exceeds max_response_bytes: {size} > {max_bytes} for {path.name}"
        )
    return path.read_text(encoding="utf-8"), path


def parse_fixture_items(
    source: dict[str, Any],
    payload_text: str,
) -> list[dict[str, Any]]:
    parser_name = str(source.get("parser") or "").strip().lower()
    kind = str(source.get("kind") or "").strip().lower()

    if parser_name == "generic_json_items" or kind in {
        "local_file_json",
        "api_json",
        "open_data_json",
    }:
        return _parse_json_items(source, payload_text)
    if parser_name == "homepage_selectors" or kind == "homepage_headlines":
        return _parse_homepage_items(source, payload_text)
    if kind in {"local_file_rss", "rss", "atom"}:
        return _parse_xml_feed(source, payload_text)
    raise UnsupportedSourceError(f"Unsupported fixture parser for source kind: {kind}")


def _normalize_item(
    source: dict[str, Any],
    raw_item: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    title = bounded_text(raw_item.get("title"), max_chars=MAX_TITLE_LENGTH)
    url = normalize_url(raw_item.get("url") or raw_item.get("link"))
    if not title or not url:
        raise NewsParserError(f"Item {index} is missing a title or URL.")
    description = bounded_text(
        raw_item.get("description") or raw_item.get("summary"),
        max_chars=MAX_DESCRIPTION_LENGTH,
    )

    raw_tags = raw_item.get("tags") or raw_item.get("categories") or []
    tags: list[str] = []
    if isinstance(raw_tags, list):
        for value in raw_tags:
            text = bounded_text(value, max_chars=64)
            if text and text not in tags:
                tags.append(text)
    elif isinstance(raw_tags, str):
        text = bounded_text(raw_tags, max_chars=64)
        if text:
            tags.append(text)

    return {
        "scope": source["scope"],
        "title": title,
        "url": url,
        "canonical_url": normalize_url(raw_item.get("canonical_url") or url),
        "description": description,
        "source_published_at": normalize_timestamp(
            raw_item.get("published_at")
            or raw_item.get("published")
            or raw_item.get("updated")
            or raw_item.get("pub_date")
            or raw_item.get("date")
        ),
        "tags": tags,
        "evidence": {
            "parser": str(source.get("parser") or source.get("kind") or "unknown"),
            "raw_index": index,
        },
    }


def _parse_json_items(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed JSON fixture: {exc}") from exc
    if isinstance(payload, dict):
        items = payload.get("items")
    else:
        items = payload
    if not isinstance(items, list):
        raise NewsParserError("JSON fixture must be a list or an object with an items list.")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise NewsParserError(f"JSON item {index} must be an object.")
        normalized.append(_normalize_item(source, item, index=index))
    return normalized


def _parse_xml_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed XML fixture: {exc}") from exc

    tag = _local_name(root.tag)
    if tag == "rss":
        return _parse_rss_feed(source, root)
    if tag == "feed":
        return _parse_atom_feed(source, root)
    raise NewsParserError(f"Unsupported feed root: {tag}")


def _parse_rss_feed(source: dict[str, Any], root: ET.Element) -> list[dict[str, Any]]:
    channel = root.find("./channel")
    if channel is None:
        raise NewsParserError("RSS fixture is missing a channel element.")
    items: list[dict[str, Any]] = []
    for index, element in enumerate(channel.findall("./item")):
        tags = [
            text
            for text in (_element_text(node) for node in element.findall("./category"))
            if text
        ]
        items.append(
            _normalize_item(
                source,
                {
                    "title": _element_text(element.find("./title")),
                    "url": _element_text(element.find("./link")),
                    "description": _element_text(element.find("./description")),
                    "published_at": _element_text(element.find("./pubDate")),
                    "tags": tags,
                },
                index=index,
            )
        )
    return items


def _parse_atom_feed(source: dict[str, Any], root: ET.Element) -> list[dict[str, Any]]:
    namespace = ""
    if root.tag.startswith("{") and "}" in root.tag:
        namespace = root.tag.split("}", 1)[0] + "}"
    items: list[dict[str, Any]] = []
    for index, element in enumerate(root.findall(f"./{namespace}entry")):
        url = ""
        for link in element.findall(f"./{namespace}link"):
            href = (link.attrib.get("href") or "").strip()
            rel = (link.attrib.get("rel") or "alternate").strip()
            if href and rel == "alternate":
                url = href
                break
            if href and not url:
                url = href
        tags = [
            link.attrib.get("term", "").strip()
            for link in element.findall(f"./{namespace}category")
        ]
        items.append(
            _normalize_item(
                source,
                {
                    "title": _element_text(element.find(f"./{namespace}title")),
                    "url": url,
                    "description": _element_text(element.find(f"./{namespace}summary"))
                    or _element_text(element.find(f"./{namespace}content")),
                    "published_at": _element_text(element.find(f"./{namespace}published"))
                    or _element_text(element.find(f"./{namespace}updated")),
                    "tags": [tag for tag in tags if tag],
                },
                index=index,
            )
        )
    return items


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list[_Node] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)

    def text_content(self) -> str:
        parts = [part.strip() for part in self.text_parts if part.strip()]
        for child in self.children:
            text = child.text_content()
            if text:
                parts.append(text)
        return " ".join(parts).strip()


class _DOMBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self._stack: list[_Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), {key.lower(): value or "" for key, value in attrs})
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if data:
            self._stack[-1].text_parts.append(data)


def _parse_homepage_items(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    selectors = source.get("selectors") or {}
    item_selector = str(selectors.get("item") or "").strip()
    title_selector = str(selectors.get("title") or "").strip()
    url_selector = str(selectors.get("url") or "").strip()
    description_selector = str(selectors.get("description") or "").strip()
    if not all((item_selector, title_selector, url_selector)):
        raise NewsParserError("Homepage fixtures require item, title, and url selectors.")

    builder = _DOMBuilder()
    builder.feed(payload_text)
    base_url = str(source.get("homepage_url") or source.get("url") or "")

    items: list[dict[str, Any]] = []
    for index, node in enumerate(_find_matching_nodes(builder.root, item_selector)):
        title_node = _first_matching_descendant(node, title_selector)
        url_node = _first_matching_descendant(node, url_selector)
        description_node = (
            _first_matching_descendant(node, description_selector)
            if description_selector
            else None
        )
        href = ""
        if url_node is not None:
            href = (url_node.attrs.get("href") or "").strip()
        items.append(
            _normalize_item(
                source,
                {
                    "title": title_node.text_content() if title_node else None,
                    "url": urljoin(base_url, href),
                    "description": description_node.text_content() if description_node else None,
                },
                index=index,
            )
        )
    return items


def _element_text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    if element.text is None:
        return None
    text = " ".join(element.text.split()).strip()
    return text or None


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_matching_nodes(root: _Node, selector_text: str) -> list[_Node]:
    selectors = [_parse_simple_selector(part) for part in selector_text.split(",") if part.strip()]
    matches: list[_Node] = []

    def visit(node: _Node) -> None:
        if any(_matches_selector(node, selector) for selector in selectors):
            matches.append(node)
        for child in node.children:
            visit(child)

    for child in root.children:
        visit(child)
    return matches


def _first_matching_descendant(root: _Node, selector_text: str) -> _Node | None:
    matches = _find_matching_nodes(root, selector_text)
    return matches[0] if matches else None


def _parse_simple_selector(text: str) -> dict[str, str | None]:
    text = text.strip()
    selector = {"tag": None, "id": None, "class": None}
    if not text:
        return selector

    tag = text
    if "#" in tag:
        tag, selector_id = tag.split("#", 1)
        selector["id"] = selector_id.strip() or None
    if "." in tag:
        tag, selector_class = tag.split(".", 1)
        selector["class"] = selector_class.strip() or None
    tag = tag.strip()
    selector["tag"] = tag.lower() or None
    return selector


def _matches_selector(node: _Node, selector: dict[str, str | None]) -> bool:
    tag = selector["tag"]
    selector_id = selector["id"]
    selector_class = selector["class"]
    if tag and node.tag != tag:
        return False
    if selector_id and (node.attrs.get("id") or "").strip() != selector_id:
        return False
    if selector_class:
        classes = {part for part in (node.attrs.get("class") or "").split() if part}
        if selector_class not in classes:
            return False
    return True
