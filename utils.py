import datetime


def time_this(func):
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        data = func(*args, **kwargs)
        end = datetime.datetime.now()
        print(f"Duration <<{func.__name__}>>: {end-start}")
        return data
    return wrapper