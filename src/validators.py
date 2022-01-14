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
    "collection_name": { "type": "string" },
    "layers": {
      "type": "array",
      "items": { "$ref": "#/$defs/layer" }
    },
    "size": { "type": "number" },
    "token_name": { "type": "string" },
  },
  
  "required": ["collection_name", "layers", "size", "token_name"],
  
  "$defs": {
    "sub_dir": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "values": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "sub_layer_path": { "type": "string" },
        "filenames": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "weights": {
          "type": "array",
          "items": {
            "type": "number"
          }
        },
        "overall_weight": {
          "type": "number",
      },
      "required": ["name", "values", "sub_layer_path", "filenames", "weights", "overall_weight"]
    }
    "layer": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "has_sub_layers": { "type": "boolean" },
        "sub_layers": {
          "type": "array",
          "items": { "$ref": "#/$defs/sub_dir" }
        },
        "values": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "layer_path": { "type": "string" },
        "filenames": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "weights": {
          "type": "array",
          "items": {
            "type": "number"
          }
        }
      },
      "required": ["name", "has_sub_layers", "layer_path"]
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

def validate_layer_details(layer, is_sub_layer = False, parent_path = ''):
  name = layer['name']
  filenames = layer['filenames']
  layer_path = layer['layer_path']
  values = layer['values']
  weights = layer['weights']

  if is_sub_layer:
    sub_layer_path = layer['sub_layer_path']
  else:
    layer_path = layer['layer_path']

  relative_trait_path = os.path.relpath(f'../data/{layer_path}', current_path)
  if not os.path.isdir(relative_trait_path):
    print(f'Error: Directory {relative_trait_path} does not exist in the directory data!')
    sys.exit(7)

  length = len(values)
  if any(len(lst) != length for lst in [values, filenames, weights]):
    print(f'Error: Properties "values", "filenames", and "weights" have different lengths in layer "{name}"!')
    sys.exit(8)

  if sum(weights) != 100:
    print(f'Error: The sum of the weights in layer "{name}" is not equal to 100!')
    sys.exit(9)

  for i, filename in enumerate(filenames):
    if is_sub_layer:
      file_path = os.path.relpath(f'../data/{parent_path}/{layer_path}/{sub_layer_path}', current_path)
    else:
      file_path = os.path.relpath(f'../data/{layer_path}/{filename}', current_path)
    
    if os.path.isfile(file_path) and filename.endswith('.png'):
      open_image(file_path)
    else:
      print(f'Error: File "{file_path}" does not exists or has the wrong extension (only png are allowed)!')
      sys.exit(10)

@utils.timer
def validate_layer(layer):
  name = layer['name']
  has_sub_layers = layer['has_sub_layers']
  layer_path = layer['layer_path']

  if has_sub_layers:
    sub_layers_weight = 0;

    for sub_layer in layer.sub_layers:
      sub_layers_weight += sub_layer.overall_weight
      validate_layer_details(sub_layer, True, layer_path)

    if sub_layers_weight != 100:
      print(f'Error: The sum of the weights of the sub layers in layer "{name}" is not equal to 100!')
      sys.exit(13)
  else:
    validate_layer_details(layer)

@utils.timer
def validate_config_obj(config_obj):
  try:
    validate(instance=config_obj, schema=config_schema)
  except jsonschema.exceptions.ValidationError as err:
    print(err)
    print("Supplied JSON config file is invalid!")
    sys.exit(6)

  collection_name = config_obj['collection_name']
  layers = config_obj['layers']
  size = config_obj['size']
  token_name = config_obj['token_name']

  for layer in layers:
    validate_layer(layer)

  images_per_layer = []
  for layer in layers:
    images_per_layer.append(len(layer['filenames']))

  if math.prod(images_per_layer) < size:
    print(f'Error: There are not enough assets to generate a collection of size "{size}"!')
    sys.exit(11)

  return collection_name, layers, size, token_name
