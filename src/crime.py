import requests
import matplotlib.pyplot as plt



def get_lat_long_from_postcode(postcode):
    response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
    if response.status_code != 200:
        return None, None
    return response.json()["result"]["latitude"], response.json()["result"]["longitude"]


def get_crimes_from_lat_long(lat, long):
    response = requests.get(f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={long}")
    if response.status_code != 200:
        return None
    return response.json()


def save_to_plot_at(crimes, filepath):
    category_counts = {}
    for crime in crimes:
        category = crime['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    categories = list(category_counts.keys())
    counts = list(category_counts.values())

    plt.figure(figsize=(8, 6))
    plt.bar(categories, counts, color='skyblue')
    plt.xlabel('Category')
    plt.ylabel('Count')
    plt.title('Count of Categories')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig(filepath)


def create_plot_from_postcode_at(postcode, filepath):
    lat, long = get_lat_long_from_postcode(postcode)
    save_to_plot_at(get_crimes_from_lat_long(lat, long), filepath)


lat, long = get_lat_long_from_postcode("M146AL")
get_crimes_from_lat_long(lat, long)
