from fastapi import File
from app.config.settings import settings
from langchain_community.document_loaders import  PyMuPDFLoader 
from docx import Document
import tempfile

class FileHandler:
     @staticmethod
     async def file_handler(file: bytes, extension: str): 
          try:
               supported = ['.pdf', '.docx']
               if extension not in supported:
                    return "Unsupported file format"

               with tempfile.NamedTemporaryFile(delete=True, suffix=extension) as temp_file:
                    temp_file.write(file)
                    temp_file.flush()  
                    
                    temp_file_path = temp_file.name
                    
                    if extension == '.pdf': loader = PyMuPDFLoader(temp_file_path)
                    elif extension == '.docx': doc = Document(temp_file_path) 

                    if loader :
                         docs = loader.load()
                         full_text = " ".join([doc.page_content for doc in docs])
                    elif doc :
                         full_text = " ".join([para.text for para in doc.paragraphs])
                    else :
                         full_text = temp_file_path.read()
                    
                    return full_text[:1500] if len(full_text) > 1500 else full_text

          except Exception as e:
               return f"Error processing file: {str(e)}"

