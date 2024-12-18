import os


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

LOCAL_DIR = os.path.join(CURRENT_DIR, ".local")
if not os.path.exists(LOCAL_DIR):
    os.makedirs(LOCAL_DIR)
