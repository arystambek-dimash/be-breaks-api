import hashlib


def generate_image_hash(image_data: bytes) -> str:
    return hashlib.sha256(image_data).hexdigest()
