import csv
import re


def join_and_lower(message):
    return message.replace(" ", "").lower()


class AllBikes:
    def __init__(self):
        self.csv_file = open('bikes/all_bikez_curated.csv', newline='', encoding='utf-8')
        self.csv_reader = csv.DictReader(self.csv_file)

    def find(self, bike):
        self.csv_file.seek(0)

        search_year = re.findall(r'\b(19\d{2}|20\d{2})\b', bike)
        if search_year:
            search_year = search_year[0]
        search_brand_and_model = re.sub(r'\b(19\d{2}|20\d{2})\b', '', bike).strip()

        def row_to_message(row, initial_message=""):
            message = initial_message
            for key in row:
                message += f"{key}: {row[key]}\n"
            return message

        fallback = None

        for row in self.csv_reader:
            if join_and_lower(search_brand_and_model) == join_and_lower(row["Brand"] + row["Model"]):
                fallback = row
                print(fallback["Brand"] + fallback["Model"])
                if not search_year:
                    return row_to_message(row)
                if search_year == row["Year"]:
                    return row_to_message(row)

        if fallback:
            return row_to_message(fallback, "Couldn't find that year, found latest model\n")
        else:
            return fallback
