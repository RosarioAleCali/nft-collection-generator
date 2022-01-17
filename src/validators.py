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
    "layers": {
      "type": "array",
      "items": { "$ref": "#/$defs/layer" }
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
    }
  },
  
  "required": [
    "artist",
    "collection_name",
    "creators",
    "layers",
    "only_one_of_traits",
    "only_one_of_traits_weights",
    "size",
    "token_name",
    "trait_categories"
  ],
  
  "$defs": {
    "layer": {
      "type": "object",
      "properties": {
        "layer_name": { "type": "string" },
        "file_paths": {
          "type": "array",
          "items": { "type": "string" }
        },
        "trait_categories": {
          "type": "array",
          "items": { "type": "string" }
        },
        "trait_values": {
          "type": "array",
          "items": { "type": "string" }
        },
        "trait_weights": {
          "type": "array",
          "items": { "type": "number" }
        },
      },
      "required": ["layer_name", "file_paths", "trait_categories", "trait_values", "trait_weights"]
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

def validate_layer_object(layer, PIL_images):
  sum_of_weights = int(sum(layer['trait_weights']))

  length = len(layer['file_paths'])
  if any(len(lst) != length for lst in [layer['file_paths'], layer['trait_categories'], layer['trait_values'], layer['trait_weights']]):
    print(f'Error: Some properties in layer {layer["layer_name"]} have different lengths.')
    print(f'file_paths: {len(layer["file_paths"])}')
    print(f'trait_categories: {len(layer["trait_categories"])}')
    print(f'trait_values: {len(layer["trait_values"])}')
    print(f'trait_weights: {len(layer["trait_weights"])}')
    sys.exit(8)

  if sum_of_weights != 100:
      print(f'Error: The sum of the weights in layer {layer["layer_name"]} is not equal to 100!')
      print(f'The sum is {sum_of_weights}')
      sys.exit(9)

  for file_path, trait_value in zip(layer['file_paths'], layer['trait_values']):
    path = os.path.relpath(f'../data/{file_path}', current_path)
  
    if os.path.isfile(path) and file_path.endswith('.png'):
      PIL_images[trait_value] = open_image(path)
    else:
      print(f'Error: File "{file_path}" does not exists or has the wrong extension (only .PNGs are allowed)!')
      sys.exit(10)

@utils.timer
def validate_config_obj(config_obj, PIL_images):
  try:
    validate(instance=config_obj, schema=config_schema)
  except jsonschema.exceptions.ValidationError as err:
    print(err.message)
    print("Supplied JSON config file is invalid!")
    sys.exit(6)

  layers = config_obj['layers']
  images_per_layer = []

  for layer in layers:
    images_per_layer.append(len(layer['file_paths']))
    validate_layer_object(layer, PIL_images)
 
  # TODO: verify this math is correct
  if math.prod(images_per_layer) < config_obj['size']:
    print(f'Error: There are not enough assets to generate a collection of size {config_obj["size"]}!')
    sys.exit(11)
