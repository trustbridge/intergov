class DiscreteGenericMessageFilter:
    def __init__(self):
        self.fields = (
            "sender", "receiver",
            "subject", "obj", "predicate")
        self._allow_any = {}
        self._whitelist = {}
        self._blacklist = {}
        for f in self.fields:
            self._allow_any[f] = False
            self._whitelist[f] = []
            self._blacklist[f] = []

    def whitelist(self, field, value):
        if field not in self.fields:
            raise Exception("invalid message field")
        if value in self._blacklist[field]:
            self._blacklist[field].remove(value)
        if value not in self._whitelist[field]:
            self._whitelist[field].append(value)

    def blacklist(self, field, value):
        if field not in self.fields:
            raise Exception("invalid message field")
        if value in self._whitelist[field]:
            self._whitelist[field].remove(value)
        if value not in self._blacklist[field]:
            self._blacklist[field].append(value)

    def allow_any(self, field):
        if field not in self.fields:
            raise Exception("invalid message field")
        if not self._allow_any[field]:
            self._allow_any[field] = True

    def disallow_any(self, field):
        if field not in self.fields:
            raise Exception("invalid message field")
        if self._allow_any[field]:
            self._allow_any[field] = False

    def screen_message(self, msg):
        """
        Return True if the message shall not pass.
        """
        # block all messages if a field is neither allow_any or whitelisted
        for field in self.fields:
            if not self._allow_any[field]:
                if field not in self._whitelist.keys():
                    return True

        # blacklist has presedence over allow_any
        for field in self.fields:
            if msg.kwargs[field] in self._blacklist[field]:
                return True

        # block if neither allow_any or whitelisted
        for field in self.fields:
            if self._allow_any[field]:
                continue
            else:
                if msg.kwargs[field] in self._whitelist[field]:
                    continue
                else:
                    return True

        return False
