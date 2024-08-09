def expires_in(seconds: int):
    import time
    return int(time.time())+seconds
