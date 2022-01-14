import math
import os
from PIL import Image
import random
import utils

all_images_combinations = []

pil_images = {}

current_path = os.path.dirname(__file__)

def open_image(file_path):
  pil_images[values[i]] = Image.open(file_path).convert('RGBA')

def create_new_image(layers, tokenId):
  new_image = {}

  for layer in layers:
    if layer.has_sub_layers:
      for sub_layer in layer.sub_layers:
        new_image[layer['name']] = random.choices(layer['values'], (100 * (layer['overall_weight'] / layer['weights']))[0]
        new_image['tokenId'] = tokenId
    else:
      new_image[layer['name']] = random.choices(layer['values'], layer['weights'])[0]
      new_image['tokenId'] = tokenId

  if new_image in all_images_combinations:
    return create_new_image(layers, tokenId)
  else:
    return new_image

@utils.timer
def generate_images_combinations(layers, size, collection_name):
  place_value = int(math.log10(size)) + 1

  for i in range(size):
    new_image = create_new_image(layers, f'{(i + 1):0{place_value}}')

    all_images_combinations.append(new_image)

  filename = f'{collection_name}-tokens_info.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  with open(file_path, 'w') as file:
    json.dump(all_images_combinations, file, indent=2)

# TODO: Refactor this function
@utils.timer
def count_traits(layers, collection_name):
  trait_count = {}

  for layer in layers:
    trait_count[layer['name']] = {}

    for value in layer['values']:
      trait_count[layer['name']][value] = 0

  for image in all_images_combinations:
    for layer in layers:
      trait_count[layer['name']][image[layer['name']]] += 1

  filename = f'{collection_name}-trait_count.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  with open(file_path, 'w') as file:
    json.dump(trait_count, file, indent=2)

def stack_images(images):
  final_image = None

  for previous, current in zip(images, images[1:]):
    if previous is not None and current is not None:
      first_image = final_image if final_image is not None else previous
      second_image = current

      final_image = Image.alpha_composite(first_image, second_image)

  return final_image

@utils.timer
def generate_images(layers, collection_name, token_name):
  output_dir = os.path.relpath(f'../data/{collection_name}', current_path)

  if os.path.exists(output_dir) and os.path.isdir(output_dir):
    shutil.rmtree(output_dir)

  os.mkdir(output_dir)

  for image_to_create in all_images_combinations:
    # Open images
    images = []

    for layer in layers:
      image = pil_images[image_to_create[layer['name']]]
      images.append(image)

    # Combine images
    final_image = stack_images(images)

    # Save images
    rgb_image = final_image.convert('RGB')
    rgb_image.save(f'{output_dir}/{token_name}-{image_to_create["tokenId"]}.png')

@utils.timer
def validate_uniqueness():
  seen = []

  if any(i in seen or seen.append(i) for i in all_images_combinations):
    print('Error: Not all images are unique!')
    sys.exit(12)
