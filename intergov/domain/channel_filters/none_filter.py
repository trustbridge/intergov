class NoneFilter:
    """
    A stupid Channel Filter that lets everything through.
    """
    def screen_message(self, msg):
        return False
