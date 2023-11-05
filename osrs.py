from osrsbox import items_api


class OSRSItems:

    all_items = items_api.load()

    def get_examine_text_from_item_name(self, item_name):
        print("Examining " + item_name)
        try:
            return self.all_items.lookup_by_item_name(item_name).examine
        except ValueError:
            return "No examine text found"
