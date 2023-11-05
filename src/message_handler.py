import fbchat

import cookies
import sensitive
import openai
import people
import osrs
import generate_image
import crime
import bikes

from itertools import islice


class MessageHandler(fbchat.Client):
    osrs_items = osrs.OSRSItems()
    people_to_respond_to = []
    respond_to = people.RespondTo(people_to_respond_to)
    all_bikes = bikes.AllBikes()

    @staticmethod
    def message_object(emoji_size=None, reply_to_id=None, sticker=None, text=None):
        return fbchat.Message(emoji_size=emoji_size, sticker=sticker, text=text, reply_to_id=reply_to_id)

    def onMessage(
            self,
            mid=None,
            author_id=None,
            message=None,
            message_object=None,
            thread_id=None,
            thread_type=fbchat.ThreadType.USER,
            ts=None,
            metadata=None,
            msg=None,
    ):
        if author_id != self.uid:
            match message_object.text.split()[0]:
                case "!genfill":
                    image_url = generate_image.get_filled_url_from(message_object.text.replace("!generate ", ""),
                                                                   "group_full.png", "group.png")
                    self.sendRemoteImage(image_url, self.message_object(), thread_id=thread_id,
                                         thread_type=thread_type)

                case "!gen":
                    image_url = generate_image.get_url_from(message_object.text.replace("!gen ", ""))
                    self.sendRemoteImage(image_url, self.message_object(), thread_id=thread_id,
                                         thread_type=thread_type)

                case "!examine":
                    message = self.message_object()
                    message.text = self.osrs_items.get_examine_text_from_item_name(
                        message_object.text.replace("!examine ", ""))
                    self.send(message, thread_id=thread_id, thread_type=thread_type)

                case "!echoimages":
                    for image in islice(self.fetchThreadImages(thread_id), 100):
                        if not hasattr(image, 'thumbnail_url'):
                            continue
                        self.sendRemoteImage(image.thumbnail_url, self.message_object(), thread_id=thread_id,
                                             thread_type=thread_type)

                case "!randomimage":
                    image_count_in_thread = 0
                    for count, image in enumerate(islice(self.fetchThreadImages(thread_id), 10000)):
                        image_count_in_thread = count
                    print(image_count_in_thread)

                case "!bike":
                    message = self.message_object()
                    message.reply_to_id = message_object.uid
                    print("searching for " + message_object.text.replace("!bike ", "").strip())
                    bike_info = self.all_bikes.find(message_object.text.replace("!bike ", "").strip())
                    if bike_info:
                        message.text = bike_info
                    else:
                        message.text = "No info for this bike"
                    self.send(message, thread_id=thread_id, thread_type=thread_type)

                case "!crime":
                    crime.create_plot_from_postcode_at(message_object.text.replace("!crime ", ""), "tmp_plot.png")
                    self.sendLocalImage("tmp_plot.png", self.message_object(), thread_id=thread_id,
                                        thread_type=thread_type)

                case _:
                    if self.fetchUserInfo(author_id)[author_id].name not in self.people_to_respond_to:
                        return
                    message = self.message_object()
                    message.text = \
                        self.respond_to.get_response_from_name_and_message(
                            self.fetchUserInfo(author_id)[author_id].name, message_object.text)
                    self.send(message, thread_id=thread_id, thread_type=thread_type)


def start():
    openai.api_key = sensitive.api_key
    client = MessageHandler(sensitive.email, sensitive.password, session_cookies=cookies.read())
    cookies.store(client.getSession())
    client.listen()
