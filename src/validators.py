from imaging import open_image
import jsonschema
from jsonschema import Draft202012Validator
from jsonschema import validate
import math
import os
import shutil
import sys
import utils

current_path = os.path.dirname(__file__)

config_schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",

  "title": "Schema for the config object",
  "description": "A configuration object for the NFT Collection Generator",
  
  "type": "object",
  "properties": {
    "artist": { "type": "string" },
    "collection_name": { "type": "string" },
    "creators": { "type": "string" },
    "images": {
      "type": "array",
      "items": { "$ref": "#/$defs/image" }
    },
    "layer_levels": {
      "type": "array",
      "items": { "type": "number" }
    },
    "only_one_of_traits": {
      "type": "array",
      "items": { "type": "string" }
    },
    "only_one_of_traits_weights": {
      "type": "array",
      "items": { "type": "number" }
    },
    "size": { "type": "number" },
    "token_name": { "type": "string" },
    "trait_categories": {
      "type": "array",
      "items": { "type": "string" }
    },
  },
  
  "required": [
    "artist",
    "collection_name",
    "creators",
    "images",
    "size",
    "token_name",
    "only_one_of_traits",
    "only_one_of_traits_weights"
  ],
  
  "$defs": {
    "image": {
      "type": "object",
      "properties": {
        "file_path": { "type": "string" },
        "layer_level": { "type": "number" },
        "trait_category": { "type": "string" },
        "trait_value": { "type": "string" },
        "weight": { "type": "number" },
      },
      "required": ["file_path", "layer_level", "trait_category", "trait_value", "weight"]
    }
  }
}

@utils.timer
def validate_schema():
  try:
    Draft202012Validator.check_schema(config_schema)
  except jsonschema.SchemaError as err:
    print(err)
    print("Schema Error: check the 'config_schema'")
    sys.exit(1)

def validate_command_line_arguments():
  if len(sys.argv) > 2:
    print('Invalid arguments!')
    print('Usage: main.py [path-to-config-file-in-data-directory]')
    sys.exit(2)

  return sys.argv

def validate_image_object(image, PIL_images):
  file_path = os.path.relpath(f'../data/{image["file_path"]}', current_path)

  if os.path.isfile(file_path) and image["file_path"].endswith('.png'):
    PIL_images[image["trait_value"]] = open_image(file_path)
  else:
    print(f'Error: File "{file_path}" does not exists or has the wrong extension (only .png is allowed)!')
    sys.exit(10)

@utils.timer
def validate_config_obj(config_obj, PIL_images):
  try:
    validate(instance=config_obj, schema=config_schema)
  except jsonschema.exceptions.ValidationError as err:
    print(err)
    print("Supplied JSON config file is invalid!")
    sys.exit(6)

  artist = config_obj['artist']
  collection_name = config_obj['collection_name']
  creators = config_obj['creators']
  images = config_obj['images']
  layer_levels = config_obj['layer_levels']
  size = config_obj['size']
  only_one_of_traits = config_obj['only_one_of_traits']
  only_one_of_traits_weights = config_obj['only_one_of_traits_weights']
  token_name = config_obj['token_name']
  trait_categories = config_obj['trait_categories']

  images_per_layer = dict.fromkeys(layer_levels, 0)
  total_weights = dict.fromkeys(layer_levels, 0)

  for image in images:
    validate_image_object(image, PIL_images)

    images_per_layer[image['layer_level']] += 1
    total_weights[image['layer_level']] += image['weight']

  for key, value in total_weights.items():
    if int(value) != 100:
      print(f'Error: The sum of the weights in layer "{key}" is not equal to 100!')
      sys.exit(9) 

  # TODO: verify this math is correct
  if math.prod(images_per_layer.values()) < size:
    print(f'Error: There are not enough assets to generate a collection of size "{size}"!')
    sys.exit(11)

  return artist, creators, collection_name, images, layer_levels, only_one_of_traits, only_one_of_traits_weights, size, token_name, trait_categories
