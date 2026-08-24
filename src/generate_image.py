import base64

import openai

import sensitive

client = openai.OpenAI(api_key=sensitive.api_key)

image_size = "1024x1024"
image_quality = "low"


def save_generated_at(message, filepath):
    print("Generating from " + message)
    response = client.images.generate(
        model="gpt-image-1",
        prompt=message,
        n=1,
        size=image_size,
        quality=image_quality,
    )
    write_image_at(response, filepath)


def save_filled_at(message, full_image_path, mask_image_path, filepath):
    print("Fill generating from " + message)
    with open(full_image_path, "rb") as image, open(mask_image_path, "rb") as mask:
        response = client.images.edit(
            model="gpt-image-1",
            image=image,
            mask=mask,
            prompt=message,
            n=1,
            size=image_size,
            quality=image_quality,
        )
    write_image_at(response, filepath)


def write_image_at(response, filepath):
    with open(filepath, "wb") as file:
        file.write(base64.b64decode(response.data[0].b64_json))