def assert_equal(a: str, b: str):
    if a != b:
        raise Exception(f"'{a}' different from '{b}'")