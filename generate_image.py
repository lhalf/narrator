import openai


def get_url_from(message):
    print("Generating from " + message)
    response = openai.Image.create(
        prompt=message,
        n=1,
        size="256x256",
    )
    return response["data"][0]["url"]


def get_filled_url_from(message, full_image_path, mask_image_path):
    print("Fill generating from " + message)
    response = openai.Image.create_edit(
        image=open(full_image_path, "rb"),
        mask=open(mask_image_path, "rb"),
        prompt=message,
        n=1,
        size="256x256"
    )
    return response['data'][0]['url']