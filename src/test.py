import json
import jsonschema
from jsonschema import Draft202012Validator
from jsonschema import validate
import os
import sys

current_path = os.path.dirname(__file__)

config_schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",

  "title": "Schema for the testing config object",
  "description": "A configuration object for testing script",

  "type": "object",
  "properties": {
    "collection_name": { "type": "string" },
    "has_properties": {
      "type": "array",
      "items": { "type": "string" }
    },
    "properties": {
      "type": "array",
      "items": { "type": "string" }
    },
    "token_info_filepath": { "type": "string" },
    "key": { "type": "string" }
  },

  "required": [
    "collection_name",
    "has_properties",
    "properties",
    "token_info_filepath",
    "key"
  ]
}

def main():
  # Test config file
  try:
    Draft202012Validator.check_schema(config_schema)
  except jsonschema.SchemaError as err:
    print(err)
    print("Schema Error: check the 'config_schema'")
    sys.exit(1)

  # Check if filename for config file is in command line arguments
  if len(sys.argv) != 2:
    print('Error: command line arguments are missing the config filename')
    sys.exit(2)
  
  filename = sys.argv[1]

  if not filename.endswith('.json'):
    print('Error: Config file must be a .json file!')
    sys.exit(3)

  filepath = os.path.relpath(f'../data/{filename}', current_path)

  try:
    with open(filepath, 'r') as file:
      data = json.load(file)
  except FileNotFoundError:
    print(f'Error: File {filename} does not exist in the directory data!')
    sys.exit(4)
  except json.decoder.JSONDecodeError:
    print('Error: Ensure JSON in config file is valid!')
    sys.exit(5)

  # Open file to test
  filename = data["token_info_filepath"]
  filepath = os.path.relpath(f'../data/{filename}', current_path)

  try:
    with open(filepath, 'r') as file:
      tokens = json.load(file)
  except FileNotFoundError:
    print(f'Error: File {filename} does not exist in the data directory')
    sys.exit(6)
  except json.decoder.JSONDecodeError:
    print('Error: Ensure JSON file is valid!')
    sys.exit(7)

  # Input list of properties to check for
  has_properties = data["has_properties"]

  # Loop through list and check for missing keys
  count = 0
  for has_property in has_properties:
    for token in tokens:
      if has_property not in token:
        count += 1
        print(f'Token {token["TokenId"]} is missing key {has_property}')

  if count != 0:
    print(f'Your tokens have some missing properties.')
    print(f'Total Count: {count}')
    sys.exit(8)

  # Check for uniqueness of tokens, Key (aka. TokenId) is obviously omitted
  properties = data["properties"]
  seen = []
  duplicates = []

  for token in tokens:
    shared_items = {}

    for seen_token in seen:
      shared_items = {k: token[k] for k in token if k in seen_token and token[k] == seen_token[k]}
    
    if len(shared_items.keys()) >= len(properties):
      print('Duplicates found!')
      print(token)
      print(seen_token)
      sys.exit(9)
    else:
      seen.append(token)

  # Counting traits again
  trait_count = {}

  for property in properties:
    trait_count[property] = {}

  for token in tokens:
    for property in properties:
      if token[property] != "None" and token[property] in trait_count[property]:
        trait_count[property][token[property]] += 1
      else:
        trait_count[property][token[property]] = 1

  filename = f'{data["collection_name"]}-trait_count.json'
  filepath = os.path.relpath(f'../data/{filename}', current_path)
  with open(filepath, 'w') as file:
    json.dump(trait_count, file, indent=2)

  print('Done!')

if __name__== '__main__':
  main()
