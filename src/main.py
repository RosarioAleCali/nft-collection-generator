import imaging
import utils
import validators

PIL_images = {}

def main():
  validators.validate_schema()
  command_line_arguments = validators.validate_command_line_arguments()
  config_obj = utils.open_config_file(command_line_arguments)
  validators.validate_config_obj(config_obj, PIL_images)
  utils.initialize_dirs(config_obj['collection_name'])
  imaging.generate_images_combinations(config_obj)
  imaging.validate_uniqueness()
  imaging.generate_images(PIL_images, config_obj['collection_name'], config_obj['token_name'])

if __name__== '__main__':
  main()
