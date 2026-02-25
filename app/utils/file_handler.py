from app.config.settings import settings
import fitz  
from docx import Document
import tempfile
import os


class FileHandler:
     @staticmethod
     async def file_handler(file: bytes, extension: str) -> str:
          try:
               supported = ['pdf', 'docx']  # No dot, to match .split(".")[-1]
               if extension not in supported:
                    return "Unsupported file format"

               suffix = f".{extension}"

               # delete=False so the file persists on disk when loaders open it
               with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(file)
                    temp_file_path = temp_file.name

               try:
                    if extension == 'pdf':
                         doc = fitz.open(temp_file_path)
                         full_text = ""
                         for page in doc:
                              full_text += page.get_text()

                    elif extension == 'docx':
                         doc = Document(temp_file_path)
                         full_text = " ".join([para.text for para in doc.paragraphs])

               finally:
                    os.remove(temp_file_path)  # Clean up manually since delete=False

               return full_text

          except Exception as e:
               return f"Error processing file: {str(e)}"