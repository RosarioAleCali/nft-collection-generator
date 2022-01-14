import json
import os
import sys
from time import perf_counter

def timer(fn):
  def inner(*args, **kwargs):
    start_time = perf_counter()
    to_execute = fn(*args, **kwargs)
    end_time = perf_counter()
    execution_time = end_time - start_time
    print(f'{fn.__name__} took {execution_time:.8f}s to execute')
    return to_execute

  return inner

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
