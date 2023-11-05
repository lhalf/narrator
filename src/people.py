import sensitive
import chat
import generate_text


class RespondTo:
    def __init__(self, activate_list):
        self.chat_history_dict = {}
        for name in activate_list:
            self.chat_history_dict[name] = chat.Chat()

    def get_response_from_name_and_message(self, name, message):
        if name not in self.chat_history_dict:
            return
        print("Replying to " + name)
        self.chat_history_dict[name].add_message_from(message, "user")
        return generate_text.from_messages(sensitive.setup_messages.get(name) + self.chat_history_dict[name].messages)



