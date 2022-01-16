import imaging
import utils
import validators

PIL_images = {}

def main():
  validators.validate_schema()
  command_line_arguments = validators.validate_command_line_arguments()
  config_obj = utils.open_config_file(command_line_arguments)
  artist, creators, collection_name, images, layer_levels, only_one_of_traits, only_one_of_traits_weights, size, token_name, trait_categories = validators.validate_config_obj(config_obj, PIL_images)
  layers = imaging.generate_layers(images, layer_levels)
  utils.initialize_dirs(collection_name)
  imaging.generate_images_combinations(artist, creators, collection_name, layers, only_one_of_traits, only_one_of_traits_weights, size, trait_categories, token_name)
  imaging.validate_uniqueness()
  imaging.generate_images(PIL_images, collection_name, token_name)

if __name__== '__main__':
  main()
