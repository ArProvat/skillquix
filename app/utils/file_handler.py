import fitz
import pdfplumber
from docx import Document
import tempfile
import os


class FileHandler:
     @staticmethod
     async def file_handler(file: bytes, extension: str) -> str:
          try:
               supported = ['pdf', 'docx']
               if extension not in supported:
                    return "Unsupported file format"

               suffix = f".{extension}"

               with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(file)
                    temp_file_path = temp_file.name

               try:
                    if extension == 'pdf':
                         full_text = FileHandler._extract_pdf(temp_file_path)
                    elif extension == 'docx':
                         full_text = FileHandler._extract_docx(temp_file_path)
               finally:
                    os.remove(temp_file_path)

               return full_text

          except Exception as e:
               return f"Error processing file: {str(e)}"

     # ------------------------------------------------------------------ #
     #  PDF                                                                 #
     # ------------------------------------------------------------------ #
     @staticmethod
     def _extract_pdf(path: str) -> str:
          output = []

          with pdfplumber.open(path) as pdf:
               for page in pdf.pages:
                    # --- 1. grab tables first & remember their bounding boxes ---
                    tables = page.find_tables()
                    table_bboxes = [t.bbox for t in tables]

                    for table in tables:
                         rows = table.extract()
                         if not rows:
                              continue
                         md = FileHandler._rows_to_markdown(rows)
                         if md:
                              output.append(md)

                    # --- 2. extract text that does NOT overlap any table bbox ---
                    if table_bboxes:
                         # crop away table regions so text isn't duplicated
                         remaining = page
                         for bbox in table_bboxes:
                              try:
                                   remaining = remaining.filter(
                                        lambda obj, bb=bbox: not FileHandler._in_bbox(obj, bb)
                                   )
                              except Exception:
                                   pass
                         text = remaining.extract_text() or ""
                    else:
                         text = page.extract_text() or ""

                    if text.strip():
                         output.append(text.strip())

          # fallback: if pdfplumber got nothing, use PyMuPDF
          if not any(output):
               doc = fitz.open(path)
               output = [page.get_text() for page in doc]

          return "\n\n".join(filter(None, output))

     # ------------------------------------------------------------------ #
     #  DOCX                                                                #
     # ------------------------------------------------------------------ #
     @staticmethod
     def _extract_docx(path: str) -> str:
          """
          Walks the document body in order so that paragraphs and tables
          appear in the same sequence as in the original file.
          """
          from lxml import etree  # bundled with python-docx

          WNS_P  = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
          WNS_TBL = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"
          WNS_TR  = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"
          WNS_TC  = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"

          doc = Document(path)
          output = []

          for child in doc.element.body:
               tag = child.tag

               # ── plain paragraph ──────────────────────────────────────────
               if tag == WNS_P:
                    text = "".join(node.text or "" for node in child.iter()
                                   if node.tag.endswith("}t"))
                    if text.strip():
                         output.append(text.strip())

               # ── table ────────────────────────────────────────────────────
               elif tag == WNS_TBL:
                    rows_data = []
                    for tr in child.findall(f".//{WNS_TR}"):
                         row = []
                         for tc in tr.findall(f".//{WNS_TC}"):
                              cell_text = "".join(
                                   node.text or "" for node in tc.iter()
                                   if node.tag.endswith("}t")
                              ).strip()
                              row.append(cell_text)
                              if any(row):
                                   rows_data.append(row)

                    md = FileHandler._rows_to_markdown(rows_data)
                    if md:
                         output.append(md)

          return "\n\n".join(output)

     # ------------------------------------------------------------------ #
     #  Helpers                                                             #
     # ------------------------------------------------------------------ #
     @staticmethod
     def _rows_to_markdown(rows: list[list]) -> str:
          """Convert a 2-D list of cells into a GitHub-flavoured markdown table."""
          if not rows:
               return ""

          # normalise every cell to str and strip whitespace
          cleaned = [[str(cell or "").strip() for cell in row] for row in rows]

          # pad all rows to the same column count
          col_count = max(len(r) for r in cleaned)
          padded = [r + [""] * (col_count - len(r)) for r in cleaned]

          header    = "| " + " | ".join(padded[0]) + " |"
          separator = "| " + " | ".join(["---"] * col_count) + " |"
          body      = ["| " + " | ".join(row) + " |" for row in padded[1:]]

          return "\n".join([header, separator] + body)

     @staticmethod
     def _in_bbox(obj: dict, bbox: tuple) -> bool:
          """Return True if a pdfplumber object's centre lies inside bbox."""
          x0, top, x1, bottom = bbox
          ox = (obj.get("x0", 0) + obj.get("x1", 0)) / 2
          oy = (obj.get("top", 0) + obj.get("bottom", 0)) / 2
          return x0 <= ox <= x1 and top <= oy <= bottom