import csv
import re

import Levenshtein

bikes_file = 'src/all_bikez_curated.csv'


def join_and_lower(message):
    return message.replace(" ", "").lower()


class AllBikes:
    def __init__(self):
        with open(bikes_file, newline='', encoding='utf-8') as csv_file:
            self.rows = list(csv.DictReader(csv_file))

    @staticmethod
    def row_to_message(row, initial_message=""):
        message = initial_message
        for key in row:
            if row[key]:
                message += f"{key}: {row[key]}\n"
        return message

    def find(self, bike):
        search_year = re.findall(r'\b(19\d{2}|20\d{2})\b', bike)

        if search_year:
            search_year = search_year[0]
        search_brand_and_model = re.sub(r'\b(19\d{2}|20\d{2})\b', '', bike).strip()

        closest_row = None
        lev_distance = 1000
        year_lev_distance = 1000
        year_difference = 1000

        for row in self.rows:
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

                    #is the year row a valid int?
                    try:
                        int(row["Year"])
                    except ValueError:
                        continue

                    #is the year difference closer?
                    if search_year and year_difference >= abs(int(search_year) - int(row["Year"])):
                        year_difference = abs(int(search_year) - int(row["Year"]))

                        closest_row = row

            if row_lev_distance == 0 and row_year_lev_distance == 0:
                return self.row_to_message(row)

        if not closest_row:
            return "No bike found"
        return self.row_to_message(closest_row, "Closest match:\n")
