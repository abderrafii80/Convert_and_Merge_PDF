import os

def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def get_file_size_kb(path):
    return os.path.getsize(path) / 1024