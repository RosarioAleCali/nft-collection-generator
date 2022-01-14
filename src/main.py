import json
import os
import shutil
import math
import random
import sys
import jsonschema
from jsonschema import validate
from jsonschema import Draft202012Validator
from PIL import Image 
from time import perf_counter

all_images_combinations = []

pil_images = {}

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

def timer(fn):
  def inner(*args, **kwargs):
    start_time = perf_counter()
    to_execute = fn(*args, **kwargs)
    end_time = perf_counter()
    execution_time = end_time - start_time
    print(f'{fn.__name__} took {execution_time:.8f}s to execute')
    return to_execute

  return inner

@timer
def validate_schema():
  try:
    Draft202012Validator.check_schema(config_schema)
  except jsonschema.SchemaError as err:
    print(err)
    print("Schema Error: check the 'config_schema'")
    sys.exit(1)

def validate_command_line_arguments(arguments):
  arguments_length = len(arguments)

  if arguments_length > 2:
    print('Invalid arguments!')
    print('Usage: main.py [path-to-config-file-in-data-directory]')
    sys.exit(2)

  return arguments

def open_config_file(arguments):
  filename = arguments[1] if len(arguments) == 2 else input('Enter the config filename: ')

  if not filename.endswith('.json'):
    print('Error: Config file must be a .json file!')
    sys.exit(3)

  file_path = os.path.relpath(f'../data/{filename}', current_path)

  try:
    with open(file_path, 'r') as file:
      data = json.load(file)
  except FileNotFoundError:
    print(f'Error: File {filename} does not exist in the directory data!')
    sys.exit(4)
  except json.decoder.JSONDecodeError:
    print('Error: Ensure JSON in config file is valid!')
    sys.exit(5)

  return data

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
      pil_images[values[i]] = Image.open(file_path).convert('RGBA')
    else:
      print(f'Error: File "{file_path}" does not exists or has the wrong extension (only png are allowed)!')
      sys.exit(10)

@timer
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

@timer
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

@timer
def generate_images_combinations(layers, size, collection_name):
  place_value = int(math.log10(size)) + 1

  for i in range(size):
    new_image = create_new_image(layers, f'{(i + 1):0{place_value}}')

    all_images_combinations.append(new_image)

  filename = f'{collection_name}-tokens_info.json'
  file_path = os.path.relpath(f'../data/{filename}', current_path)
  with open(file_path, 'w') as file:
    json.dump(all_images_combinations, file, indent=2)

@timer
def validate_uniqueness():
  seen = []

  if any(i in seen or seen.append(i) for i in all_images_combinations):
    print('Error: Not all images are unique!')
    sys.exit(12)

# TODO: Refactor this function
@timer
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

@timer
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

def main():
  # Validate our schema
  validate_schema()

  # Validate command line arguments
  command_line_arguments = validate_command_line_arguments(sys.argv)
  
  # Read config from JSON files
  config_obj = open_config_file(command_line_arguments)

  # Validate config obj
  collection_name, layers, size, token_name = validate_config_obj(config_obj)

  # Generate image combinations
  generate_images_combinations(layers, size, collection_name)

  # Validate uniqueness
  validate_uniqueness()

  # Trait counting
  count_traits(layers, collection_name)

  # Generate images
  generate_images(layers, collection_name, token_name)

if __name__== '__main__':
  main()
