"""
Gieni OS - Notion to PDF Master Exporter
Exports the entire Gieni OS Notion Book/Wiki, all core architecture pages,
SOPs, and databases to individual executive PDFs and a single merged Master PDF book.
"""

import os
import sys
import re
import argparse
import requests
from typing import Dict, Any, List, Optional, Tuple
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

# Configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"

# Gieni OS Master Database (Contains all 25 core OS pages)
GIENI_OS_DB_ID = "3e0b5bd1-d90c-816c-a3fe-c114522ab51a"

# Sub-Databases
KB_DB_ID = "3e0b5bd1-d90c-812c-9c65-d25cefd633a3"
OPPORTUNITIES_DB_ID = "3e0b5bd1-d90c-81e6-bb4d-c1bc60166a40"
COUNTIES_DB_ID = "3e0b5bd1-d90c-8105-b6fd-ef9a8371d96b"
CLIENTS_DB_ID = "3e0b5bd1-d90c-810e-a326-de5677c60e18"
TASKS_DB_ID = "3e0b5bd1-d90c-810c-98c7-c8a8297dd47c"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

RECURSIVE_BLOCK_TYPES = {
    "column_list", "column", "toggle", "callout",
    "bulleted_list_item", "numbered_list_item", "table", "synced_block"
}


class NotionBlockParser:
    """Recursively converts Notion API rich text and block structures to styled HTML."""

    @staticmethod
    def _apply_annotations(text: str, annotations: Dict[str, Any], link: Optional[Dict[str, Any]]) -> str:
        if annotations.get("bold"):
            text = f"<strong>{text}</strong>"
        if annotations.get("italic"):
            text = f"<em>{text}</em>"
        if annotations.get("strikethrough"):
            text = f"<del>{text}</del>"
        if annotations.get("underline"):
            text = f"<u>{text}</u>"
        if annotations.get("code"):
            text = f"<code>{text}</code>"
        color = annotations.get("color")
        if color and color != "default":
            text = f"<span class='color-{color}'>{text}</span>"
        if link and link.get("url"):
            text = f"<a href='{link['url']}' target='_blank'>{text}</a>"
        return text

    @classmethod
    def rich_text_to_html(cls, rich_text_list: List[Dict[str, Any]]) -> str:
        if not rich_text_list:
            return ""
        html_parts = []
        for item in rich_text_list:
            text = item.get("text", {}).get("content", "")
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            link = item.get("text", {}).get("link")
            annotations = item.get("annotations", {})
            html_parts.append(cls._apply_annotations(text, annotations, link))
        return "".join(html_parts).replace("\n", "<br>")

    @classmethod
    def _render_paragraph(cls, b: Dict[str, Any]) -> str:
        rt = b.get("paragraph", {}).get("rich_text", [])
        content = cls.rich_text_to_html(rt)
        return f"<p>{content}</p>" if content.strip() else "<p class='empty-para'></p>"

    @classmethod
    def _render_heading(cls, b: Dict[str, Any], level: int) -> str:
        key = f"heading_{level}"
        rt = b.get(key, {}).get("rich_text", [])
        return f"<h{level}>{cls.rich_text_to_html(rt)}</h{level}>"

    @classmethod
    def _render_list_item(cls, b: Dict[str, Any], b_type: str) -> str:
        rt = b.get(b_type, {}).get("rich_text", [])
        children = b.get("children", [])
        nested = f"\n{cls.blocks_to_html(children)}" if children else ""
        return f"<li>{cls.rich_text_to_html(rt)}{nested}</li>"

    @classmethod
    def _render_todo(cls, b: Dict[str, Any]) -> str:
        to_do = b.get("to_do", {})
        checked = to_do.get("checked", False)
        rt = to_do.get("rich_text", [])
        box = "&#9745;" if checked else "&#9744;"
        strike = "style='text-decoration: line-through; color: #94a3b8;'" if checked else ""
        return f"<div class='todo-item'><span class='checkbox'>{box}</span> <span {strike}>{cls.rich_text_to_html(rt)}</span></div>"

    @classmethod
    def _render_quote(cls, b: Dict[str, Any]) -> str:
        rt = b.get("quote", {}).get("rich_text", [])
        children = b.get("children", [])
        nested = f"\n{cls.blocks_to_html(children)}" if children else ""
        return f"<blockquote>{cls.rich_text_to_html(rt)}{nested}</blockquote>"

    @classmethod
    def _render_callout(cls, b: Dict[str, Any]) -> str:
        callout = b.get("callout", {})
        icon_data = callout.get("icon", {})
        icon = icon_data.get("emoji", "&#128161;") if icon_data.get("type") == "emoji" else "&#128161;"
        rt = callout.get("rich_text", [])
        children = b.get("children", [])
        nested = f"\n{cls.blocks_to_html(children)}" if children else ""
        return f"<div class='callout'><span class='callout-icon'>{icon}</span> <div class='callout-text'>{cls.rich_text_to_html(rt)}{nested}</div></div>"

    @classmethod
    def _render_code(cls, b: Dict[str, Any]) -> str:
        code_obj = b.get("code", {})
        lang = code_obj.get("language", "")
        rt = code_obj.get("rich_text", [])
        code_text = "".join(t.get("text", {}).get("content", "") for t in rt)
        code_text = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre><code class='language-{lang}'>{code_text}</code></pre>"

    @classmethod
    def _render_table(cls, b: Dict[str, Any]) -> str:
        children = b.get("children", [])
        if not children:
            return ""
        rows = []
        for row in children:
            cells = row.get("table_row", {}).get("cells", [])
            cells_html = "".join(f"<td>{cls.rich_text_to_html(c)}</td>" for c in cells)
            rows.append(f"<tr>{cells_html}</tr>")
        return f"<table class='notion-table'>{''.join(rows)}</table>"

    @classmethod
    def _render_column_list(cls, b: Dict[str, Any]) -> str:
        children = b.get("children", [])
        cols = [f"<div class='column'>{cls.blocks_to_html(col.get('children', []))}</div>" for col in children]
        return f"<div class='column-list'>{''.join(cols)}</div>"

    @classmethod
    def _render_toggle(cls, b: Dict[str, Any]) -> str:
        toggle = b.get("toggle", {})
        rt = toggle.get("rich_text", [])
        children = b.get("children", [])
        nested = cls.blocks_to_html(children) if children else ""
        return f"<details open><summary class='toggle-summary'>{cls.rich_text_to_html(rt)}</summary><div class='toggle-content'>{nested}</div></details>"

    @classmethod
    def _render_block_content(cls, b_type: str, b: Dict[str, Any]) -> Optional[str]:
        if b_type == "paragraph":
            return cls._render_paragraph(b)
        if b_type == "heading_1":
            return cls._render_heading(b, 1)
        if b_type == "heading_2":
            return cls._render_heading(b, 2)
        if b_type == "heading_3":
            return cls._render_heading(b, 3)
        if b_type in ("bulleted_list_item", "numbered_list_item"):
            return cls._render_list_item(b, b_type)
        if b_type == "to_do":
            return cls._render_todo(b)
        if b_type == "quote":
            return cls._render_quote(b)
        if b_type == "callout":
            return cls._render_callout(b)
        if b_type == "divider":
            return "<hr class='divider'>"
        if b_type == "code":
            return cls._render_code(b)
        if b_type == "table":
            return cls._render_table(b)
        if b_type == "column_list":
            return cls._render_column_list(b)
        if b_type == "toggle":
            return cls._render_toggle(b)
        if b_type == "child_page":
            cp_title = b.get("child_page", {}).get("title", "Sub-Page")
            return f"<div class='child-page-box'>&#128196; <strong>{cp_title}</strong></div>"
        if b_type == "child_database":
            cd_title = b.get("child_database", {}).get("title", "Embedded Database")
            return f"<div class='child-db-box'>&#128451; <strong>{cd_title}</strong></div>"
        if b_type == "synced_block":
            return cls.blocks_to_html(b.get("children", []))
        return None

    @classmethod
    def blocks_to_html(cls, blocks: List[Dict[str, Any]]) -> str:
        html_lines = []
        in_bullet_list = False
        in_number_list = False

        for b in blocks:
            b_type = b.get("type", "")

            # Manage list state transitions
            if b_type == "bulleted_list_item":
                if not in_bullet_list:
                    html_lines.append("<ul>")
                    in_bullet_list = True
            elif in_bullet_list:
                html_lines.append("</ul>")
                in_bullet_list = False

            if b_type == "numbered_list_item":
                if not in_number_list:
                    html_lines.append("<ol>")
                    in_number_list = True
            elif in_number_list:
                html_lines.append("</ol>")
                in_number_list = False

            rendered = cls._render_block_content(b_type, b)
            if rendered:
                html_lines.append(rendered)

        if in_bullet_list:
            html_lines.append("</ul>")
        if in_number_list:
            html_lines.append("</ol>")

        return "\n".join(html_lines)


class NotionPDFExporter:
    """Orchestrates Notion API page fetching, Playwright PDF rendering, and PDF merging."""

    def __init__(self, output_dir: str = "./exports/pdf"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _fetch_child_blocks(self, block_id: str, cursor: Optional[str]) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children"
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = self.session.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            return [], False, None
        data = resp.json()
        return data.get("results", []), data.get("has_more", False), data.get("next_cursor")

    def fetch_page_blocks_recursive(self, block_id: str) -> List[Dict[str, Any]]:
        """Recursively pulls all child blocks of a page or block with pagination."""
        all_blocks = []
        has_more = True
        cursor = None

        while has_more:
            blocks, has_more, cursor = self._fetch_child_blocks(block_id, cursor)
            for b in blocks:
                if b.get("has_children") and b.get("type") in RECURSIVE_BLOCK_TYPES:
                    b["children"] = self.fetch_page_blocks_recursive(b["id"])
                all_blocks.append(b)

        return all_blocks

    @staticmethod
    def _extract_prop_val(p_type: str, prop_val: Dict[str, Any]) -> Any:
        if p_type == "select":
            sel = prop_val.get("select")
            return sel.get("name") if sel else None
        if p_type == "status":
            st = prop_val.get("status")
            return st.get("name") if st else None
        if p_type == "number":
            return prop_val.get("number")
        if p_type == "rich_text":
            rt = prop_val.get("rich_text", [])
            text = "".join(t["plain_text"] for t in rt)
            return text if text and len(text) < 80 else None
        return None

    def extract_page_title_and_metadata(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts the page title and standard property badges."""
        props = page_data.get("properties", {})
        title = "Untitled"
        metadata = {}

        for prop_name, prop_val in props.items():
            p_type = prop_val.get("type")
            if p_type == "title":
                t_arr = prop_val.get("title", [])
                title = "".join(t["plain_text"] for t in t_arr) if t_arr else "Untitled"
            else:
                val = self._extract_prop_val(p_type, prop_val)
                if val is not None:
                    metadata[prop_name] = val

        return {
            "title": title,
            "metadata": metadata,
            "created_time": page_data.get("created_time", ""),
            "last_edited_time": page_data.get("last_edited_time", "")
        }

    def generate_html_document(self, title: str, metadata: Dict[str, Any], body_html: str, chapter_num: Optional[int] = None) -> str:
        """Embeds body HTML inside an executive print-ready template."""
        badges_html = []
        for k, v in metadata.items():
            if k in ["Status", "Priority", "Category", "Workflow Stage", "Authority Classification", "Section"]:
                badges_html.append(f"<span class='badge badge-{k.lower().replace(' ', '-')}'><strong>{k}:</strong> {v}</span>")

        badges_str = " ".join(badges_html)
        eyebrow_text = f"GIENI OS &bull; CHAPTER {chapter_num}" if chapter_num else "GIENI OS &bull; INSTITUTIONAL SYSTEM SPECIFICATION"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{
    size: letter;
    margin: 20mm 18mm 20mm 18mm;
    @bottom-right {{
      content: "Page " counter(page);
      font-size: 8.5pt;
      color: #94a3b8;
    }}
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    line-height: 1.6;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
    background: #ffffff;
  }}

  .header-container {{
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 14px;
    margin-bottom: 22px;
  }}

  .system-eyebrow {{
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #2563eb;
    margin-bottom: 4px;
  }}

  h1.page-title {{
    font-size: 20pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 10px 0;
    line-height: 1.25;
  }}

  .badges-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
  }}

  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 8pt;
    font-weight: 500;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #e2e8f0;
  }}

  .badge-status {{ background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }}
  .badge-priority {{ background: #fef2f2; color: #b91c1c; border-color: #fecaca; }}
  .badge-category {{ background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }}

  .body-content {{
    margin-top: 14px;
  }}

  h1 {{ font-size: 15pt; font-weight: 700; color: #0f172a; margin-top: 22px; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }}
  h2 {{ font-size: 13pt; font-weight: 600; color: #1e293b; margin-top: 18px; margin-bottom: 6px; }}
  h3 {{ font-size: 11.5pt; font-weight: 600; color: #334155; margin-top: 14px; margin-bottom: 4px; }}

  p {{
    margin: 0 0 10px 0;
    font-size: 10.5pt;
  }}

  p.empty-para {{
    height: 6px;
    margin: 0;
  }}

  ul, ol {{
    margin: 4px 0 10px 22px;
    padding: 0;
  }}

  li {{
    margin-bottom: 4px;
    font-size: 10.5pt;
  }}

  blockquote {{
    border-left: 3.5px solid #3b82f6;
    margin: 12px 0;
    padding: 8px 16px;
    background: #f8fafc;
    color: #334155;
    font-style: italic;
    border-radius: 0 4px 4px 0;
  }}

  .callout {{
    display: flex;
    align-items: flex-start;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px 14px;
    margin: 12px 0;
  }}

  .callout-icon {{
    font-size: 14pt;
    margin-right: 12px;
    line-height: 1.2;
  }}

  .callout-text {{
    flex: 1;
    font-size: 10pt;
  }}

  .todo-item {{
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    font-size: 10pt;
  }}

  .todo-item .checkbox {{
    margin-right: 8px;
    font-size: 11pt;
  }}

  hr.divider {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 20px 0;
  }}

  pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 12px 14px;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 9pt;
    line-height: 1.45;
    overflow-x: auto;
    margin: 12px 0;
  }}

  code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    background: #f1f5f9;
    color: #0f172a;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 9pt;
  }}

  pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
  }}

  table.notion-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 9.5pt;
  }}

  table.notion-table td, table.notion-table th {{
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
  }}

  table.notion-table tr:nth-child(even) {{
    background: #f8fafc;
  }}

  .column-list {{
    display: flex;
    gap: 16px;
    margin: 12px 0;
  }}

  .column {{
    flex: 1;
  }}

  details {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 10px 0;
  }}

  summary.toggle-summary {{
    font-weight: 600;
    cursor: pointer;
  }}

  .toggle-content {{
    margin-top: 8px;
    padding-left: 12px;
  }}

  .child-page-box, .child-db-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 6px 0;
    font-size: 9.5pt;
    color: #334155;
  }}

  .footer-container {{
    border-top: 1px solid #e2e8f0;
    margin-top: 30px;
    padding-top: 8px;
    font-size: 8pt;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
  }}
</style>
</head>
<body>

<div class="header-container">
  <div class="system-eyebrow">{eyebrow_text}</div>
  <h1 class="page-title">{title}</h1>
  <div class="badges-row">
    {badges_str}
  </div>
</div>

<div class="body-content">
  {body_html}
</div>

<div class="footer-container">
  <span>Gieni OS &bull; Canonical System Manual</span>
  <span>CTO / Systems Architecture Approved</span>
</div>

</body>
</html>
"""

    def export_page_to_pdf(self, page_id: str, custom_filename: Optional[str] = None, chapter_num: Optional[int] = None) -> Optional[str]:
        """Fetches a Notion page, recursively parses its blocks, and produces a PDF."""
        url = f"https://api.notion.com/v1/pages/{page_id}"
        resp = self.session.get(url, timeout=12)
        if resp.status_code != 200:
            print(f"[!] Error fetching page {page_id}: {resp.status_code}")
            return None

        page_data = resp.json()
        meta_info = self.extract_page_title_and_metadata(page_data)
        title = meta_info["title"]

        # Fetch child blocks recursively
        blocks = self.fetch_page_blocks_recursive(page_id)
        body_html = NotionBlockParser.blocks_to_html(blocks)

        # Assemble full styled HTML
        full_html = self.generate_html_document(title, meta_info["metadata"], body_html, chapter_num=chapter_num)

        # Clean Filename
        if not custom_filename:
            prefix = f"{chapter_num:02d}_" if chapter_num is not None else ""
            safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)[:45].strip('_')
            custom_filename = f"{prefix}{safe_title}.pdf"
        elif not custom_filename.endswith(".pdf"):
            custom_filename += ".pdf"

        pdf_path = os.path.join(self.output_dir, custom_filename)

        # Render with Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(full_html, wait_until="networkidle")
            page.pdf(
                path=pdf_path,
                format="Letter",
                print_background=True,
                margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}
            )
            browser.close()

        print(f"  [+] PDF Saved: {custom_filename}")
        return pdf_path

    def _query_database_pages(self, database_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        all_pages = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            payload: Dict[str, Any] = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = self.session.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                print(f"[!] Error querying database {database_id}: {resp.status_code}")
                break

            data = resp.json()
            results = data.get("results", [])
            all_pages.extend(results)

            if limit and len(all_pages) >= limit:
                return all_pages[:limit]

            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return all_pages

    @staticmethod
    def _merge_pdfs(pdf_paths: List[str], master_path: str) -> None:
        try:
            writer = PdfWriter()
            for pdf_file in pdf_paths:
                writer.append(pdf_file)
            with open(master_path, "wb") as f_out:
                writer.write(f_out)
            print(f"[SUCCESS] Master Book compiled: {os.path.abspath(master_path)} ({len(pdf_paths)} chapters)")
        except Exception as e:
            print(f"[!] Error merging master PDF: {e}")

    def export_gieni_os_manual(self, merge_master: bool = True) -> List[str]:
        """
        Exports the entire Gieni OS Notion Book (all 25 pages) to individual numbered PDFs,
        and combines them into a single comprehensive Master Book PDF.
        """
        print(f"\n" + "="*80)
        print(f" EXPORTING COMPLETE GIENI OS NOTION BOOK (Database: {GIENI_OS_DB_ID})")
        print("="*80)

        all_pages = self._query_database_pages(GIENI_OS_DB_ID)
        print(f"Discovered {len(all_pages)} core Gieni OS pages to export.\n")

        os_dir = os.path.join(self.output_dir, "Gieni_OS_Full_Book")
        os.makedirs(os_dir, exist_ok=True)
        orig_dir = self.output_dir
        self.output_dir = os_dir

        generated_pdfs = []
        for idx, page in enumerate(all_pages, 1):
            p_id = page.get("id")
            meta = self.extract_page_title_and_metadata(page)
            safe_title = meta['title'].encode('ascii', 'replace').decode()
            print(f"[{idx:02d}/{len(all_pages)}] Exporting Chapter: '{safe_title}'...")
            pdf_path = self.export_page_to_pdf(p_id, chapter_num=idx)
            if pdf_path:
                generated_pdfs.append(pdf_path)

        if merge_master and generated_pdfs:
            master_pdf_path = os.path.join(orig_dir, "Gieni_OS_Complete_Book_v2.pdf")
            print(f"\nMerging {len(generated_pdfs)} chapters into Master Book: {master_pdf_path}...")
            self._merge_pdfs(generated_pdfs, master_pdf_path)

        self.output_dir = orig_dir
        return generated_pdfs

    def export_database_pages(self, database_id: str, db_name: str, limit: Optional[int] = None) -> List[str]:
        """Exports all pages in a given Notion database as individual PDFs."""
        print(f"\n--- Exporting Database: {db_name} ---")
        all_pages = self._query_database_pages(database_id, limit=limit)
        print(f"Found {len(all_pages)} records to export.")

        sub_dir = os.path.join(self.output_dir, re.sub(r'[^a-zA-Z0-9_\-]', '_', db_name))
        os.makedirs(sub_dir, exist_ok=True)
        orig_dir = self.output_dir
        self.output_dir = sub_dir

        generated_pdfs = []
        for idx, page in enumerate(all_pages, 1):
            p_id = page.get("id")
            meta = self.extract_page_title_and_metadata(page)
            print(f"[{idx}/{len(all_pages)}] '{meta['title']}'...")
            pdf_path = self.export_page_to_pdf(p_id)
            if pdf_path:
                generated_pdfs.append(pdf_path)

        self.output_dir = orig_dir
        return generated_pdfs


def _dispatch_export_mode(exporter: NotionPDFExporter, args: argparse.Namespace) -> None:
    if args.target in ("os", "all"):
        exporter.export_gieni_os_manual(merge_master=not args.no_merge)
    if args.target in ("kb", "all"):
        exporter.export_database_pages(KB_DB_ID, "Knowledge_Base_SOPs", limit=args.limit)
    if args.target in ("opportunities", "all"):
        exporter.export_database_pages(OPPORTUNITIES_DB_ID, "Probate_Opportunities", limit=args.limit or 15)
    if args.target == "id":
        if not args.id:
            print("[!] Error: --id is required when --target id is specified.")
            sys.exit(1)
        try:
            exporter.export_page_to_pdf(args.id)
        except Exception:
            exporter.export_database_pages(args.id, "Custom_Notion_Database", limit=args.limit)


def main():
    parser = argparse.ArgumentParser(description="Gieni OS - Notion to PDF Master Exporter")
    parser.add_argument("--target", choices=["os", "kb", "opportunities", "all", "id"], default="os",
                        help="Target to export: 'os' (Entire Gieni OS Book - all 25 chapters + Master Merged PDF), 'kb' (Knowledge Base SOPs), 'opportunities' (Probate Opportunity Files), 'all' (Everything), or 'id' (single page/db)")
    parser.add_argument("--id", type=str, default=None, help="Specific Page or Database ID when --target id is selected")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to export")
    parser.add_argument("--no-merge", action="store_true", help="Do not merge into a single master PDF book")
    parser.add_argument("--output-dir", type=str, default="./exports/pdf", help="Output directory for generated PDFs")

    args = parser.parse_args()
    exporter = NotionPDFExporter(output_dir=args.output_dir)

    print("\n" + "="*80)
    print(" GIENI OS -- NOTION TO PDF MASTER EXPORT PIPELINE")
    print(f" Mode: {args.target} | Output Directory: {os.path.abspath(args.output_dir)}")
    print("="*80)

    _dispatch_export_mode(exporter, args)

    print("\n" + "="*80)
    print(" EXPORT PIPELINE COMPLETE")
    print(f" Files written to: {os.path.abspath(args.output_dir)}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
