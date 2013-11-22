def max_size(text, size):
    if len(text) > size:
        return text[:size] + '...'
    else:
        return text