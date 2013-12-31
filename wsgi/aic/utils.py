def max_size(text, size):
    if len(text) > size:
        return text[:size] + '...'
    else:
        return text

def take(array,count):
    i = 0
    while i < count and i < len(array):
        yield array[i]
        i += 1

def drop(array,count):
    i = 0
    while i < count:
        i += 1
    while i < len(array):
        yield array[i]
        i += 1
