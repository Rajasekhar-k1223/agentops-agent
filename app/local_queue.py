# app/local_queue.py

import os
import json
import uuid
import logging

class LocalQueue:
    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def enqueue(self, data, prefix="payload"):
        file_name = f"{prefix}_{uuid.uuid4().hex}.json"
        full_path = os.path.join(self.path, file_name)
        with open(full_path, "w") as f:
            json.dump(data, f)
        logging.info(f"⏳ Saved data locally: {file_name}")

    def flush(self, post_func):
        files = os.listdir(self.path)
        for file in files:
            file_path = os.path.join(self.path, file)
            try:
                with open(file_path) as f:
                    payload = json.load(f)
                post_func(payload)
                os.remove(file_path)
                logging.info(f"✅ Flushed saved file: {file}")
            except Exception as e:
                logging.error(f"⚠️ Could not flush {file}: {e}")
