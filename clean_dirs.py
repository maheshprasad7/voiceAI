import shutil
import os

dirs_to_remove = ["audio", "config", "conversation", "stt", "tts", "llm", "memory", "future"]

for d in dirs_to_remove:
    path = os.path.join(os.getcwd(), d)
    if os.path.exists(path):
        print(f"Removing {path}")
        shutil.rmtree(path)
    else:
        print(f"Not found: {path}")
