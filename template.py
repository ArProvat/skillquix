import os
from pathlib import Path
import logging

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

list_of_files = [
    "app/DB/mongodb/router.py",
    "app/DB/mongodb/schema.py",
    "app/DB/mongodb/mongodb.py",
    "app/DB/mongodb/__init__.py",
    "app/DB/vectorDB/router.py",
    "app/DB/vectorDB/schema.py",
    "app/DB/vectorDB/vectordb.py",
    "app/DB/vectorDB/__init__.py",
    "app/data/.gitkeep", # Placeholder to ensure the folder is tracked
    "app/Services/demo_1/router.py",
    "app/Services/demo_1/schema.py",
    "app/Services/demo_1/code.py",
    "app/Services/demo_1/__init__.py",
    "app/Services/demo_2/router.py",
    "app/Services/demo_2/schema.py",
    "app/Services/demo_2/code.py",
    "app/Services/demo_2/__init__.py",
    "app/config/settings.py",
    "app/config/__init__.py",
    "app/moduls/auth/auth.py",
    "app/moduls/auth/__init__.py",
    "app/prompt/prompt.py",
    "app/prompt/__init__.py",
    "utilits/__init__.py",
    "requirements.txt",
    "main.py",
    "Dockerfile",
    "docker-compose.yml",
    ".gitignore",
    "setup.py"
    ".dockerignore",
    ".env"
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file: {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
        logging.info(f"Created empty file: {filepath}")
    else:
        logging.info(f"{filename} already exists")

logging.info("GenAI Project Structure created successfully!")