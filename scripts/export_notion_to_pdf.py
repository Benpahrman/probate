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
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

# Configuration
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
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

class NotionBlockParser:
    """Recursively converts Notion API rich text and block structures to styled HTML."""

    @staticmethod
    def rich_text_to_html(rich_text_list: List[Dict[str, Any]]) -> str:
        if not rich_text_list:
            return ""
        html_parts = []
        for item in rich_text_list:
            text = item.get("text", {}).get("content", "")
            # Escape HTML special characters
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            link = item.get("text", {}).get("link")
            annotations = item.get("annotations", {})

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
                url = link.get("url")
                text = f"<a href='{url}' target='_blank'>{text}</a>"

            html_parts.append(text)
        return "".join(html_parts).replace("\n", "<br>")

    @classmethod
    def blocks_to_html(cls, blocks: List[Dict[str, Any]]) -> str:
        html_lines = []
        in_bullet_list = False
        in_number_list = False

        for b in blocks:
            b_type = b.get("type")

            # Manage list state transitions
            if b_type == "bulleted_list_item":
                if not in_bullet_list:
                    html_lines.append("<ul>")
                    in_bullet_list = True
            else:
                if in_bullet_list:
                    html_lines.append("</ul>")
                    in_bullet_list = False

            if b_type == "numbered_list_item":
                if not in_number_list:
                    html_lines.append("<ol>")
                    in_number_list = True
            else:
                if in_number_list:
                    html_lines.append("</ol>")
                    in_number_list = False

            # Block Type Renderers
            if b_type == "paragraph":
                rt = b.get("paragraph", {}).get("rich_text", [])
                content = cls.rich_text_to_html(rt)
                if content.strip():
                    html_lines.append(f"<p>{content}</p>")
                else:
                    html_lines.append("<p class='empty-para'></p>")

            elif b_type == "heading_1":
                rt = b.get("heading_1", {}).get("rich_text", [])
                html_lines.append(f"<h1>{cls.rich_text_to_html(rt)}</h1>")

            elif b_type == "heading_2":
                rt = b.get("heading_2", {}).get("rich_text", [])
                html_lines.append(f"<h2>{cls.rich_text_to_html(rt)}</h2>")

            elif b_type == "heading_3":
                rt = b.get("heading_3", {}).get("rich_text", [])
                html_lines.append(f"<h3>{cls.rich_text_to_html(rt)}</h3>")

            elif b_type == "bulleted_list_item":
                rt = b.get("bulleted_list_item", {}).get("rich_text", [])
                children = b.get("children", [])
                nested_html = f"\n{cls.blocks_to_html(children)}" if children else ""
                html_lines.append(f"<li>{cls.rich_text_to_html(rt)}{nested_html}</li>")

            elif b_type == "numbered_list_item":
                rt = b.get("numbered_list_item", {}).get("rich_text", [])
                children = b.get("children", [])
                nested_html = f"\n{cls.blocks_to_html(children)}" if children else ""
                html_lines.append(f"<li>{cls.rich_text_to_html(rt)}{nested_html}</li>")

            elif b_type == "to_do":
                to_do = b.get("to_do", {})
                checked = to_do.get("checked", False)
                rt = to_do.get("rich_text", [])
                box = "&#9745;" if checked else "&#9744;"
                strike = "style='text-decoration: line-through; color: #94a3b8;'" if checked else ""
                html_lines.append(f"<div class='todo-item'><span class='checkbox'>{box}</span> <span {strike}>{cls.rich_text_to_html(rt)}</span></div>")

            elif b_type == "quote":
                rt = b.get("quote", {}).get("rich_text", [])
                children = b.get("children", [])
                nested_html = f"\n{cls.blocks_to_html(children)}" if children else ""
                html_lines.append(f"<blockquote>{cls.rich_text_to_html(rt)}{nested_html}</blockquote>")

            elif b_type == "callout":
                callout = b.get("callout", {})
                icon_data = callout.get("icon", {})
                icon = icon_data.get("emoji", "&#128161;") if icon_data.get("type") == "emoji" else "&#128161;"
                rt = callout.get("rich_text", [])
                children = b.get("children", [])
                nested_html = f"\n{cls.blocks_to_html(children)}" if children else ""
                html_lines.append(f"<div class='callout'><span class='callout-icon'>{icon}</span> <div class='callout-text'>{cls.rich_text_to_html(rt)}{nested_html}</div></div>")

            elif b_type == "divider":
                html_lines.append("<hr class='divider'>")

            elif b_type == "code":
                code_obj = b.get("code", {})
                lang = code_obj.get("language", "")
                rt = code_obj.get("rich_text", [])
                code_text = "".join(t.get("text", {}).get("content", "") for t in rt)
                code_text = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_lines.append(f"<pre><code class='language-{lang}'>{code_text}</code></pre>")

            elif b_type == "table":
                children = b.get("children", [])
                if children:
                    html_lines.append("<table class='notion-table'>")
                    for row in children:
                        cells = row.get("table_row", {}).get("cells", [])
                        html_lines.append("<tr>")
                        for cell in cells:
                            html_lines.append(f"<td>{cls.rich_text_to_html(cell)}</td>")
                        html_lines.append("</tr>")
                    html_lines.append("</table>")

            elif b_type == "column_list":
                children = b.get("children", [])
                html_lines.append("<div class='column-list'>")
                for col in children:
                    col_children = col.get("children", [])
                    html_lines.append(f"<div class='column'>{cls.blocks_to_html(col_children)}</div>")
                html_lines.append("</div>")

            elif b_type == "toggle":
                toggle = b.get("toggle", {})
                rt = toggle.get("rich_text", [])
                children = b.get("children", [])
                nested_html = cls.blocks_to_html(children) if children else ""
                html_lines.append(f"<details open><summary class='toggle-summary'>{cls.rich_text_to_html(rt)}</summary><div class='toggle-content'>{nested_html}</div></details>")

            elif b_type == "child_page":
                cp_title = b.get("child_page", {}).get("title", "Sub-Page")
                html_lines.append(f"<div class='child-page-box'>&#128196; <strong>{cp_title}</strong></div>")

            elif b_type == "child_database":
                cd_title = b.get("child_database", {}).get("title", "Embedded Database")
                html_lines.append(f"<div class='child-db-box'>&#128451; <strong>{cd_title}</strong></div>")

            elif b_type == "synced_block":
                children = b.get("children", [])
                html_lines.append(cls.blocks_to_html(children))

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

    def fetch_page_blocks_recursive(self, block_id: str) -> List[Dict[str, Any]]:
        """Recursively pulls all child blocks of a page or block with pagination."""
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/blocks/{block_id}/children"
            params = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor

            resp = self.session.get(url, params=params, timeout=12)
            if resp.status_code != 200:
                break

            data = resp.json()
            blocks = data.get("results", [])
            for b in blocks:
                # Recursively fetch nested blocks for columns, toggles, callouts, lists, tables
                if b.get("has_children"):
                    b_type = b.get("type")
                    if b_type in ["column_list", "column", "toggle", "callout", "bulleted_list_item", "numbered_list_item", "table", "synced_block"]:
                        b["children"] = self.fetch_page_blocks_recursive(b["id"])
                all_blocks.append(b)

            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return all_blocks

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
            elif p_type == "select":
                sel = prop_val.get("select")
                if sel:
                    metadata[prop_name] = sel.get("name")
            elif p_type == "status":
                st = prop_val.get("status")
                if st:
                    metadata[prop_name] = st.get("name")
            elif p_type == "number":
                num = prop_val.get("number")
                if num is not None:
                    metadata[prop_name] = num
            elif p_type == "rich_text":
                rt = prop_val.get("rich_text", [])
                text = "".join(t["plain_text"] for t in rt)
                if text and len(text) < 80:
                    metadata[prop_name] = text

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
    margin-top: 6px;
  }}

  .badge {{
    display: inline-block;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 8pt;
    color: #334155;
  }}

  .badge-status {{ background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }}
  .badge-priority {{ background: #eff6ff; border-color: #bfdbfe; color: #1e40af; }}
  .badge-category {{ background: #f8fafc; border-color: #cbd5e1; color: #475569; }}

  h1 {{ font-size: 15pt; font-weight: 700; color: #0f172a; margin-top: 22px; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; page-break-after: avoid; }}
  h2 {{ font-size: 12.5pt; font-weight: 700; color: #1e293b; margin-top: 16px; margin-bottom: 6px; page-break-after: avoid; }}
  h3 {{ font-size: 11pt; font-weight: 600; color: #334155; margin-top: 12px; margin-bottom: 4px; page-break-after: avoid; }}

  p {{ margin: 0 0 10px 0; }}
  .empty-para {{ height: 6px; margin: 0; }}

  ul, ol {{ margin: 0 0 10px 0; padding-left: 22px; }}
  li {{ margin-bottom: 4px; }}

  blockquote {{
    margin: 12px 0;
    padding: 10px 16px;
    background: #f8fafc;
    border-left: 4px solid #2563eb;
    color: #334155;
    font-style: italic;
    border-radius: 0 6px 6px 0;
  }}

  .callout {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 12px 0;
    page-break-inside: avoid;
  }}

  .callout-icon {{ font-size: 14pt; line-height: 1; }}
  .callout-text {{ flex: 1; }}

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
    color: #1e293b;
  }}

  .toggle-content {{
    margin-top: 8px;
    padding-left: 8px;
    border-left: 2px solid #cbd5e1;
  }}

  .child-page-box, .child-db-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 6px 0;
    font-size: 9.5pt;
    color: #1e293b;
  }}

  .divider {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 18px 0;
  }}

  code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    padding: 2px 4px;
    border-radius: 4px;
    color: #0f172a;
  }}

  pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8pt;
    line-height: 1.4;
  }}

  pre code {{
    background: transparent;
    color: #f8fafc;
    padding: 0;
  }}

  .notion-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 8.5pt;
  }}

  .notion-table td, .notion-table th {{
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
  }}

  .notion-table tr:nth-child(even) {{
    background: #f8fafc;
  }}

  .footer-container {{
    margin-top: 32px;
    padding-top: 10px;
    border-top: 1px solid #e2e8f0;
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

    def export_gieni_os_manual(self, merge_master: bool = True) -> List[str]:
        """
        Exports the entire Gieni OS Notion Book (all 25 pages) to individual numbered PDFs,
        and combines them into a single comprehensive Master Book PDF.
        """
        print(f"\n" + "="*80)
        print(f" EXPORTING COMPLETE GIENI OS NOTION BOOK (Database: {GIENI_OS_DB_ID})")
        print(f"="*80)

        # Query all pages in the Gieni OS master database
        all_pages = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/databases/{GIENI_OS_DB_ID}/query"
            payload = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = self.session.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                print(f"[!] Error querying Gieni OS database: {resp.status_code}")
                break

            data = resp.json()
            pages = data.get("results", [])
            all_pages.extend(pages)
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        print(f"Discovered {len(all_pages)} core Gieni OS pages to export.\n")

        # Set output subfolder
        os_dir = os.path.join(self.output_dir, "Gieni_OS_Full_Book")
        os.makedirs(os_dir, exist_ok=True)
        orig_dir = self.output_dir
        self.output_dir = os_dir

        generated_pdfs = []

        # Export each page sequentially
        for idx, page in enumerate(all_pages, 1):
            p_id = page.get("id")
            meta = self.extract_page_title_and_metadata(page)
            safe_title = meta['title'].encode('ascii', 'replace').decode()
            print(f"[{idx:02d}/{len(all_pages)}] Exporting Chapter: '{safe_title}'...")
            pdf_path = self.export_page_to_pdf(p_id, chapter_num=idx)
            if pdf_path:
                generated_pdfs.append(pdf_path)

        # Merge into single master PDF book
        if merge_master and generated_pdfs:
            master_pdf_path = os.path.join(orig_dir, "Gieni_OS_Complete_Book_v2.pdf")
            print(f"\nMerging {len(generated_pdfs)} chapters into Master Book: {master_pdf_path}...")
            try:
                writer = PdfWriter()
                for pdf_file in generated_pdfs:
                    writer.append(pdf_file)
                with open(master_pdf_path, "wb") as f_out:
                    writer.write(f_out)
                print(f"[SUCCESS] Master Book compiled: {os.path.abspath(master_pdf_path)} ({len(generated_pdfs)} chapters)")
            except Exception as e:
                print(f"[!] Error merging master PDF: {e}")

        self.output_dir = orig_dir
        return generated_pdfs

    def export_database_pages(self, database_id: str, db_name: str, limit: Optional[int] = None) -> List[str]:
        """Exports all pages in a given Notion database as individual PDFs."""
        print(f"\n--- Exporting Database: {db_name} ---")
        all_pages = []
        has_more = True
        start_cursor = None

        while has_more:
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            payload = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            resp = self.session.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                print(f"[!] Error querying database: {resp.status_code}")
                break

            data = resp.json()
            pages = data.get("results", [])
            all_pages.extend(pages)

            if limit and len(all_pages) >= limit:
                all_pages = all_pages[:limit]
                break

            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        print(f"Found {len(all_pages)} records to export.")
        generated_pdfs = []

        sub_dir = os.path.join(self.output_dir, re.sub(r'[^a-zA-Z0-9_\-]', '_', db_name))
        os.makedirs(sub_dir, exist_ok=True)
        orig_dir = self.output_dir
        self.output_dir = sub_dir

        for idx, page in enumerate(all_pages, 1):
            p_id = page.get("id")
            meta = self.extract_page_title_and_metadata(page)
            print(f"[{idx}/{len(all_pages)}] '{meta['title']}'...")
            pdf_path = self.export_page_to_pdf(p_id)
            if pdf_path:
                generated_pdfs.append(pdf_path)

        self.output_dir = orig_dir
        return generated_pdfs

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

    if args.target == "os":
        # Export the entire Gieni OS book (all 25 chapters + merged master book)
        exporter.export_gieni_os_manual(merge_master=not args.no_merge)
    elif args.target == "kb":
        exporter.export_database_pages(KB_DB_ID, "Knowledge_Base_SOPs", limit=args.limit)
    elif args.target == "opportunities":
        exporter.export_database_pages(OPPORTUNITIES_DB_ID, "Probate_Opportunities", limit=args.limit or 15)
    elif args.target == "all":
        exporter.export_gieni_os_manual(merge_master=not args.no_merge)
        exporter.export_database_pages(KB_DB_ID, "Knowledge_Base_SOPs", limit=args.limit)
        exporter.export_database_pages(OPPORTUNITIES_DB_ID, "Probate_Opportunities", limit=args.limit or 15)
    elif args.target == "id":
        if not args.id:
            print("[!] Error: --id is required when --target id is specified.")
            sys.exit(1)
        try:
            exporter.export_page_to_pdf(args.id)
        except Exception:
            exporter.export_database_pages(args.id, "Custom_Notion_Database", limit=args.limit)

    print("\n" + "="*80)
    print(" EXPORT PIPELINE COMPLETE")
    print(f" Files written to: {os.path.abspath(args.output_dir)}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
