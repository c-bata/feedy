
def social_share_plugin(callback):
    def wrapper(*args, **kwargs):
        print('This is social share plugins')
        callback(*args, **kwargs)
    return wrapper
