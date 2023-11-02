# def write_images_to_file(images):
#     for count, image in enumerate(islice(images, 1000)):
#         if not hasattr(image, 'thumbnail_url'):
#             print("Not an image, skipping")
#             continue
#         print("Saving image: " + str(count))
#         img_data = requests.get(image.thumbnail_url).content
#         with open('pictures/{}.jpg'.format(count), 'wb') as file:
#             file.write(img_data)