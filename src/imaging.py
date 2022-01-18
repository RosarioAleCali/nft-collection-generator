import math
import os
from PIL import Image
import random
import utils

current_path = os.path.dirname(__file__)

all_images_combinations = []
trait_count = {}

def open_image(file_path):
  return Image.open(file_path).convert('RGBA')

def create_new_image(config_obj, tokenId):
  output_dir = os.path.relpath(f'../data/{config_obj["collection_name"]}', current_path)

  place_value = int(math.log10(config_obj['size'])) + 1

  new_image = {}

  new_image_metadata = {
    "name": f'{config_obj["token_name"]} #{(tokenId + 1):0{place_value}}',
    "symbol": f'{config_obj["symbol"]} #{(tokenId + 1):0{place_value}}',
    "description": f'{config_obj["description"]} Number {tokenId + 1}/{config_obj["size"]}.',
    "image": f'{tokenId}.png',
    "attributes": [],
    "properties": {
      "files": [
        {
          "uri": f'{tokenId}.png',
          "type": "image/png"
        }
      ]
    }
  }

  for layer in config_obj['layers']:
    trait_index = random.choices(range(len(layer['trait_values'])), layer['trait_weights'])[0]
    trait_name = layer['trait_categories'][trait_index]
    trait_value = layer['trait_values'][trait_index]

    #TODO: check logic is correct to the specs
    # check if current trait has some special conditions
    if trait_name in config_obj['only_one_of_traits']:
      # check if image already has a special trait
      intersection = [i for i in config_obj['only_one_of_traits'] if i in new_image and new_image[i] != "None"]

      # if image already has a special trait...
      if len(intersection) > 0:
        # if the trait name is not in the image, but image already has a special trait:
        # - Set value to none
        if trait_name not in intersection:
          trait_value = "None"
      else:
        # check if quota in collection has been met. If yes, set value to None
        only_one_trait_index = config_obj['only_one_of_traits'].index(trait_name)
        trait_name_weight = config_obj['only_one_of_traits_weights'][only_one_trait_index]

        images_with_trait_name = 0

        for image in all_images_combinations:
          if trait_name in image and image[trait_name] != "None":
            images_with_trait_name += 1

        current_percentage = (images_with_trait_name * 100) / config_obj['size']

        if current_percentage > trait_name_weight:
          trait_value = "None"

    new_image[trait_name] = trait_value
    
  if new_image in all_images_combinations:
    return create_new_image(config_obj, tokenId)
  else:
    for name, value in new_image.items():
      if value != "None" and name != "artist" and name != "creators":
        new_image_metadata["attributes"].append(
          {"trait_type": name, "value": value}
        )
        trait_count[name][value] += 1

    new_image['TokenId'] = tokenId

    file_path = os.path.relpath(f'{output_dir}/{tokenId}.json', current_path)
    utils.write_json(new_image_metadata, file_path)

    return new_image

@utils.timer
def generate_images_combinations(config_obj):
  # Initialize treat counts to zero
  for trait_category in config_obj['trait_categories']:
    trait_count[trait_category] = {}

  for layer in config_obj['layers']:
    for trait_category, trait_value in zip(layer['trait_categories'], layer['trait_values']):
      trait_count[trait_category][trait_value] = 0

  # Generare image combintations for size
  for i in range(config_obj['size']):
    new_image = create_new_image(config_obj, i)
    all_images_combinations.append(new_image)

  # Write tokens info to JSON
  filename = f'{config_obj["collection_name"]}-tokens_info.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  utils.write_json(all_images_combinations, file_path)

  # Write trait count to JSON
  filename = f'{config_obj["collection_name"]}-trait_count.json'
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
    rgb_image.save(f'{output_dir}/{image_to_create["TokenId"]}.png')

@utils.timer
def validate_uniqueness():
  seen = []

  if any(i in seen or seen.append(i) for i in all_images_combinations):
    print('Error: Not all images are unique!')
    sys.exit(12)
