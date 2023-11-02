from osrsbox import items_api


class OSRSItems:

    all_items = items_api.load()

    def get_examine_text_from_item_name(self, item_name):
        print("Examining " + item_name)
        examine_text = self.all_items.lookup_by_item_name(item_name).examine
        if examine_text:
            return examine_text
        else:
            return "No examine text found"
