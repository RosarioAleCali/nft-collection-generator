import math
import os
from PIL import Image
import random
import utils

all_images_combinations = []

pil_images = {}
trait_count = {}

current_path = os.path.dirname(__file__)

def open_image(file_path):
  return Image.open(file_path).convert('RGBA')

@utils.timer
def generate_layers(images, layer_levels):
  layers = []

  for layer_level in layer_levels:
    names = []
    values = []
    weights = []

    images_per_layer = [image for image in images if image.get('layer_level') == layer_level]

    for image_per_layer in images_per_layer:
      names.append(image_per_layer['trait_category'])
      values.append(image_per_layer['trait_value'])
      weights.append(image_per_layer['weight'])

    layer = {
      'names': names,
      'values': values,
      'weights': weights,
    }
    
    layers.append(layer)

  return layers

def create_new_image(artist, creators, collection_name, layers, tokenId, only_one_of_traits, only_one_of_traits_weights, size, token_name):
  output_dir = os.path.relpath(f'../data/{collection_name}', current_path)
  
  new_image = {
    "artist": artist,
    "creators": creators,
  }

  for layer in layers:
    trait_index = random.choices(range(len(layer['values'])), layer['weights'])[0]
    trait_name = layer['names'][trait_index]
    trait_value = layer['values'][trait_index]

    #TODO: check logic is correct to the specs
    # check if current trait has some special conditions
    if trait_name in only_one_of_traits:
      # check if image already has a special trait
      intersection = [i for i in only_one_of_traits if i in new_image and new_image[i] != "None"]

      # if image already has a special trait...
      if len(intersection) > 0:
        # if the trait name is not in the image, but image already has a special trait:
        # - Set value to none
        if trait_name not in intersection:
          trait_value = "None"
      else:
        # check if quota in collection has been met. If yes, set value to None
        only_one_trait_index = only_one_of_traits.index(trait_name)
        trait_name_weight = only_one_of_traits_weights[only_one_trait_index]

        images_with_trait_name = 0

        for image in all_images_combinations:
          if trait_name in image and image[trait_name] != "None":
            images_with_trait_name += 1

        current_percentage = (images_with_trait_name * 100) / size

        if current_percentage > trait_name_weight:
          trait_value = "None"

    new_image[trait_name] = trait_value
    
  if new_image in all_images_combinations:
    return create_new_image(artist, creators, layers, tokenId, only_one_of_traits, only_one_of_traits_weights, size, token_name)
  else:
    for name, value in new_image.items():
      if value != "None" and name != "artist" and name != "creators":
        trait_count[name][value] += 1

    new_image['TokenId'] = tokenId

    file_path = os.path.relpath(f'{output_dir}/{token_name}-{tokenId}.json', current_path)
    utils.write_json(new_image, file_path)

    return new_image

@utils.timer
def generate_images_combinations(artist, creators, collection_name, layers, only_one_of_traits, only_one_of_traits_weights, size, trait_categories, token_name):
  place_value = int(math.log10(size)) + 1

  # Initialize treat counts to zero
  for trait_category in trait_categories:
    trait_count[trait_category] = {}

  for layer in layers:
    for name, value in zip(layer['names'], layer['values']):
      trait_count[name][value] = 0

  # Generare image combintations for size
  for i in range(size):
    new_image = create_new_image(artist, creators, collection_name, layers, f'{(i + 1):0{place_value}}', only_one_of_traits, only_one_of_traits_weights, size, token_name)
    all_images_combinations.append(new_image)

  # Write tokens info to JSON
  filename = f'{collection_name}-tokens_info.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  utils.write_json(all_images_combinations, file_path)

  # Write trait count to JSON
  filename = f'{collection_name}-trait_count.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  utils.write_json(trait_count, file_path)

def stack_images(images):
  final_image = None

  for previous, current in zip(images, images[1:]):
    if previous is not None and current is not None:
      first_image = final_image if final_image is not None else previous
      second_image = current

      final_image = Image.alpha_composite(first_image, second_image)

  return final_image

@utils.timer
def generate_images(PIL_images, collection_name, token_name):
  output_dir = os.path.relpath(f'../data/{collection_name}', current_path)
  for image_to_create in all_images_combinations:
    # Open images
    images = []

    for image_value in image_to_create.values():
      try:
        image = PIL_images[image_value]
        images.append(image)
      except:
        pass

    # Combine images
    final_image = stack_images(images)

    # Save images
    rgb_image = final_image.convert('RGB')
    rgb_image.save(f'{output_dir}/{token_name}-{image_to_create["TokenId"]}.png')

@utils.timer
def validate_uniqueness():
  seen = []

  if any(i in seen or seen.append(i) for i in all_images_combinations):
    print('Error: Not all images are unique!')
    sys.exit(12)
