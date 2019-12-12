import os, json, re, jinja2, sys
from jsonmerge import merge, Merger
from azure.keyvault import KeyVaultClient
from jinja2 import Environment, FileSystemLoader
from collections import ChainMap
from azure.common.client_factory import get_client_from_cli_profile

# Environment variable
# vault_url must be in the format 'https://<vaultname>.vault.azure.net'

import argparse

# Setup Azure client
client = get_client_from_cli_profile(KeyVaultClient)

def renderTemplate(vault_url, json_path, head_file, environment):
    secrets = client.get_secrets(vault_url)
    ids     = [secret.as_dict()['id'] for secret in secrets]
    secret_list = [retrieveValue(id, vault_url) for id in ids]
    secret_dict = dict(ChainMap(*secret_list))
    file_loader = FileSystemLoader(json_path)
    env         = Environment(loader=file_loader, undefined=jinja2.StrictUndefined)
    template    = env.get_template(head_file)
    head        = template.render(azurekv=secret_dict, environment=environment)
    return (head)

def retrieveValue(secret_id, vault_url):
    regex = re.compile(vault_url + 'secrets/(.*)', re.IGNORECASE)
    match = regex.search(secret_id)
    assert match, 'Failed to parse the secret name from "{id}"'.format(id=id)
    secret_name   = match.group(1)
    secret_bundle = client.get_secret(vault_url, secret_name, "")
    secret_value  = secret_bundle.value
    return ({secret_name:secret_value})

def merge_head_to_base (base, head):
    schema = {
        "properties": {
            "ConnectorGallery": {
                "type": "array",

                "mergeStrategy": "arrayMergeById",
                "mergeOptions": {"idRef": "Id"}
            }
        }
    }
    merger = Merger(schema)
    result = merger.merge(base, head)
    return result

def main(argv=sys.argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("--key-vault", 
                        default=os.environ.get('AZURE_KEY_VAULT_URL'))
    parser.add_argument('--pipeline-environment',
                        default=os.environ.get('PIPELINE_ENVIRONMENT'))

    #args = parser.parse_args(argv)
    args, unknown = parser.parse_known_args(argv)
 
    if not args.key_vault: 
        return 1 

    if not args.pipeline_environment: 
        return 1

    # # Base and environment json path
    environment = args.pipeline_environment
    vault_url   = args.key_vault
    json_path = './json/'
    base_file = 'base.json'
    head_file = 'head.json'
    appsettings_json = 'appsettings-'+ environment +'.json'

    with open(json_path + base_file) as json_file:
        base = json.load(json_file)

    try: 
        head = renderTemplate(vault_url, json_path, head_file, environment)
        head_json_output = json.loads(head)
    except Exception as e:  # find real exception type 
        sys.exit("Output template does not render as json: ", e)

    with open(json_path + appsettings_json, 'w') as outfile:
        merged_appsettings_data = merge_head_to_base(base, head_json_output)
        json.dump(merged_appsettings_data, outfile, sort_keys=True)    

    return 0 

if __name__ == '__main__':
    os._exit(main())