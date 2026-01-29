import shutil
import os
from tests.conftest import OUTPUT_DIR

print(f"purging : {OUTPUT_DIR}")
shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)
print("purging done.")
