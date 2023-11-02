class Chat:
    messages = []

    def add_message_from(self, message, role):
        self.messages.append({"role": role, "content": message})
        if len(self.messages) == 10:
            self.messages.pop(0)
