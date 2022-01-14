import imaging
import utils
import validators

def main():
  validators.validate_schema()
  command_line_arguments = validators.validate_command_line_arguments()
  config_obj = utils.open_config_file(command_line_arguments)
  collection_name, layers, size, token_name = validators.validate_config_obj(config_obj)
  imaging.generate_images_combinations(layers, size, collection_name)
  imaging.validate_uniqueness()
  imaging.count_traits(layers, collection_name)
  imaging.generate_images(layers, collection_name, token_name)

if __name__== '__main__':
  main()
