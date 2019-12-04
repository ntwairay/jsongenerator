import os, json
from deepdiff import DeepDiff  # For Deep Difference of 2 objects

# environment variable
environment        = os.environ['PIPELINE_ENVIRONMENT']

# path
json_path    = './json/'
current_file = 'appsettings-old.json'
new_file     = 'appsettings-'+environment +'.json'

def compare(current, new):
    ddiff = DeepDiff(current, new, verbose_level=0)
    updatedItems = ddiff['values_changed']
    for key, value in updatedItems.items():
         print(key)

def main():
    with open(json_path + current_file) as json_file:
        current_appsettings = json.load(json_file)
    

    with open(json_path + new_file) as json_file:
        new_appsettings = json.load(json_file)

    compare(current_appsettings, new_appsettings)

if __name__ == '__main__':
    main()