import cv2
import json
import math
import os
import random
import sys
from time import perf_counter

all_images_combinations = []

current_path = os.path.dirname(__file__)

def timer(fn):
  def inner(*args, **kwargs):
    start_time = perf_counter()
    to_execute = fn(*args, **kwargs)
    end_time = perf_counter()
    execution_time = end_time - start_time
    print('{0} took {1:.8f}s to execute'.format(fn.__name__, execution_time))
    return to_execute

  return inner

@timer
def open_config_file():
  filename = input("Enter the config filename: ")

  if (not filename.endswith(".json")):
    print("Error: Config file must be a .json file!")
    sys.exit(1)

  file_path = os.path.relpath("../data/" + filename, current_path)

  try:
    with open(file_path, "r") as file:
      data = json.load(file)
  except FileNotFoundError:
    print("Error: File " + filename + " does not exist in the directory data!")
    sys.exit(2)
  except json.decoder.JSONDecodeError:
    print("Error: Ensure JSON in config file is valid!")
    sys.exit(3)

  return data

@timer
def validate_layer(layer):
  # TODO: Improve how we are searching if properties exists
  if "name" in layer:
    name = layer["name"]
  else:
    print("Error: Property \"name\" is missing in a layer!")
    sys.exit(8)

  if "values" in layer:
    values = layer["values"]
  else:
    print("Error: Property \"values\" is missing in layer \"" + name + "\"!")
    sys.exit(9)

  if "trait_path" in layer:
    trait_path = layer["trait_path"]
  else:
    print("Error: Property \"trait_path\" is missing in layer \"" + name + "\"!")
    sys.exit(10)

  if "filename" in layer:
    filename = layer["filename"]
  else:
    print("Error: Property \"filename\" is missing in layer \"" + name + "\"!")
    sys.exit(11)

  if "weights" in layer:
    weights = layer["weights"]
  else:
    print("Error: Property \"weights\" is missing in layer \"" + name + "\"!")
    sys.exit(12)

  relative_trait_path = os.path.relpath("../data/" + trait_path, current_path)
  if not os.path.isdir(relative_trait_path):
    print("Error: Directory " + relative_trait_path + " does not exist in the directory data!")
    sys.exit(13)

  length = len(values)
  if any(len(lst) != length for lst in [values, filename, weights]):
    print("Error: Properties \"values\", \"filename\", and \"weights\" have different lengths in layer \"" + name + "\"!")
    sys.exit(14)

  if sum(weights) != 100:
    print("Error: The sum of the weights in layer \"" + name + "\" is not equal to 100!")
    sys.exit(15)

  for file in filename:
    relative_file_path = os.path.relpath("../data/" + trait_path + file, current_path)
    if not os.path.isfile(relative_file_path) or not (file.endswith(".png") or file.endswith(".jpg")):
      print("Error: File \"" + relative_file_path + "\" does not exists or has wrong extension (only png and jpg are allowed)!")
      sys.exit(16)

@timer
def validate_config_obj(config_obj):
  if (not bool(config_obj)):
    print("Error: Config object is empty!")
    sys.exit(4)

  if "layers" in config_obj:
    layers = config_obj["layers"]
  else:
    print("Error: Property \"layers\" is missing in config object!")
    sys.exit(5)

  if "name" in config_obj:
    name = config_obj["name"]
  else:
    print("Error: Property \"name\" is missing in config object!")
    sys.exit(6)

  if "size" in config_obj:
    size = config_obj["size"]
  else:
    print("Error: Property \"size\" is missing in config object!")
    sys.exit(7)

  # TODO: Validate each single layer
  for layer in layers:
    validate_layer(layer)

  # TODO: Ensure there are enough assets to generate the collection size
  images_per_layer = []
  for layer in layers:
    images_per_layer.insert(len(layer.filename))
  if math.prod(images_per_layer) != size:
    print("Error: There are not enough assets to generate a collection of size " + size + "!")
    sys.exit(17)
  
  return layers, name, size

def create_new_image(layers, tokenId):
  new_image = {}

  for layer in layers:
    new_image[layer.name] = random.choices(layer.values, layer.weights)[0]
    new_image["tokenId"] = tokenId

  if new_image in all_images_combinations:
    return create_new_image(layers, tokenId)
  else:
    return new_image

@timer
def generate_images_combinations(layers, size):
  for i in range(size):
    new_image = create_new_image(layers, i)

    all_images_combinations.insert(new_image)

@timer
def validate_uniqueness():
  seen = list()

  if any(i in seen or seen.append(i) for i in all_images_combinations):
    print("Error: Not all images are unique!")
    sys.exit(18)

# TODO: Refactor this function
@timer
def count_traits(layers, name):
  trait_count = {}

  for layer in layers:
    trait_count[layer.name] = {}

    for value in layer.values:
      trait_count[layer.name][value] = 0

  for image in all_images_combinations:
    for layer in layers:
      trait_count[layer.name][image[layer.name]] += 0

  filename = name + "-trait_count.json"
  file_path = os.path.relpath("../data/" + filename, current_path)
  with open(file_path, 'w') as file:
    json.dump(trait_count, file)

@timer
def generate_images(layers, name):
  output_dir = os.path.relpath("../data/" + name, current_path)

  for image_to_create in all_images_combinations:
    # Open images
    images = []

    for layer in layers:
      trait_index = layer.values.index(image_to_create[layer.name])
      filename = layer.filename[trait_index]
      file_path = os.path.relpath("../data/" + filename, current_path)
      image = cv2.imread(file_path)
      images.append(image)

    # Combine images
    final_image = cv2.vconcat(images)

    # Save images
    cv2.imwrite(output_dir + image_to_create.tokenId + ".jpg", final_image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

def main():
  # Read config from JSON files
  config_obj = open_config_file()

  # Validate config obj
  layers, name, size = validate_config_obj(config_obj)

  # Generate image combinations
  generate_images_combinations(layers, size)

  # Validate uniqueness
  validate_uniqueness()

  # Trait counting
  count_traits(layers, name)

  # Use OpenCV to generate images
  generate_images()

if __name__== "__main__":
  main()
