import os
import re
import uuid
from urllib.parse import urlencode

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_image(filename):
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_uploaded_file(file_storage, folder_name):
    if not file_storage or not file_storage.filename:
        return ""

    if not allowed_image(file_storage.filename):
        return ""

    folder_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder_name)
    os.makedirs(folder_path, exist_ok=True)

    original_name = secure_filename(file_storage.filename)
    base_name, extension = os.path.splitext(original_name)
    safe_name = f"{base_name}-{uuid.uuid4().hex}{extension.lower()}"
    target_path = os.path.join(folder_path, safe_name)
    file_storage.save(target_path)

    relative_path = os.path.relpath(target_path, current_app.config["UPLOAD_FOLDER"]).replace("\\", "/")
    return relative_path


def currency_value(value):
    if value is None:
        return ""
    return f"{float(value):,.2f}"


def whatsapp_url(settings, message):
    raw_number = settings.whatsapp if settings and settings.whatsapp else ""
    number = re.sub(r"\D", "", raw_number)
    if number.startswith("00"):
        number = number[2:]
    elif number.startswith("0") and len(number) in {10, 11}:
        number = f"92{number.lstrip('0')}"
    if not 7 <= len(number) <= 15:
        return None
    return f"https://wa.me/{number}?{urlencode({'text': message})}"


def whatsapp_product_url(settings, product):
    message = (
        f"Assalam-o-Alaikum, I'm interested in {product.name} "
        f"({product.model}). Please share the price and installment details."
    )
    return whatsapp_url(settings, message)
