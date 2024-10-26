def get_formatted_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_units = ["B", "KB", "MB", "GB", "TB"]
    idx = int(log(size_bytes, 1024))
    p = pow(1024, idx)
    s = round(size_bytes / p, 2)
    return f"{s} {size_units[idx]}"
