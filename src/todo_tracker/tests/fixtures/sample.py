# Sample Python file for testing TODO extraction.


def main():
    # TODO: refactor this function
    data = load_data()

    # FIXME(GH-89): race condition in concurrent access
    process(data)

    # HACK: monkey-patch for compatibility
    import os  # noqa

    # TODO(rerickso): clean up after migration
    return data


def load_data():
    # NOTE: returns empty dict if file not found
    return {}


def process(data):
    # OPTIMIZE: use batch insert instead of loop
    for key in data:
        save(key, data[key])


def save(key, value):
    pass
