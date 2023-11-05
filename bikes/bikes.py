import csv
import re

import Levenshtein


def join_and_lower(message):
    return message.replace(" ", "").lower()


class AllBikes:
    def __init__(self):
        self.csv_file = open('bikes/all_bikez_curated.csv', newline='', encoding='utf-8')
        self.csv_reader = csv.DictReader(self.csv_file)

    @staticmethod
    def row_to_message(row, initial_message=""):
        message = initial_message
        for key in row:
            if row[key]:
                message += f"{key}: {row[key]}\n"
        return message

    def find(self, bike):
        self.csv_file.seek(0)

        search_year = re.findall(r'\b(19\d{2}|20\d{2})\b', bike)
        print(search_year)

        if search_year:
            search_year = search_year[0]
        search_brand_and_model = re.sub(r'\b(19\d{2}|20\d{2})\b', '', bike).strip()

        closest_row = None
        lev_distance = 1000
        year_lev_distance = 1000
        year_difference = 1000

        for row in self.csv_reader:
            row_lev_distance = Levenshtein.distance(join_and_lower(search_brand_and_model), join_and_lower(row["Brand"] + row["Model"]))
            if search_year:
                row_year_lev_distance = Levenshtein.distance(search_year, row["Year"])
            else:
                row_year_lev_distance = 0

            #is the make and brand closer OR equal to what we currently have?
            if row_lev_distance <= lev_distance:
                #the make and brand distance was LESS then what we had
                if row_lev_distance < lev_distance:
                    closest_row = row
                    #reset years for this new closest match
                    year_lev_distance = 1000
                    year_difference = 1000

                #store current distance
                lev_distance = row_lev_distance

                #is the year distance closer OR equal to what we currently have?
                if row_year_lev_distance <= year_lev_distance:
                    year_lev_distance = row_year_lev_distance

                    #is the year difference closer?
                    if search_year and year_difference >= abs(int(search_year) - int(row["Year"])):
                        year_difference = abs(int(search_year) - int(row["Year"]))

                        closest_row = row

            if row_lev_distance == 0 and row_year_lev_distance == 0:
                return self.row_to_message(row)

        return self.row_to_message(closest_row, "Closest match:\n")
