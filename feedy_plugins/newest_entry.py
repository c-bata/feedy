
def feed_handler_wrapper(callback):
    def wrapper(*args, **kwargs):
        print('This is newest entry plugins')
        callback(*args, **kwargs)
    return wrapper


class NewestEntryPlugin:
    def setup(self, feedy):
        feedy.feed_handler = feed_handler_wrapper(feedy.feed_handler)
