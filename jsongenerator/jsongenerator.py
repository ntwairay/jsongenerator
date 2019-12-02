import os, uuid, json, re, ast
from jsonmerge import merge, Merger
from azure.keyvault import KeyVaultClient
from azure.common.credentials import ServicePrincipalCredentials
from jinja2 import Environment, FileSystemLoader
from collections import ChainMap

# Environment variable
# vault_url must be in the format 'https://<vaultname>.vault.azure.net'
azure_client_id    = os.environ['AZURE_CLIENT_ID']
azure_client_secret= os.environ['AZURE_CLIENT_SECRET']
azure_tenant_id    = os.environ['AZURE_TENANT_ID']
vault_url          = os.environ['AZURE_KEY_VAULT_URL']

# Base and environment json path
json_path = './jsongenerator/json/'
base_file = 'base.json'
head_file = 'head.json'
appsettings_json = 'appsettings.json'

# Setup Azure service principle 
credentials = ServicePrincipalCredentials(
    client_id = azure_client_id,
    secret    = azure_client_secret,
    tenant    = azure_tenant_id
)
# create Azure Client
client = KeyVaultClient(credentials)

def renderTemplate(vault_url):
    secrets = client.get_secrets(vault_url)
    ids     = [secret.as_dict()['id'] for secret in secrets]
    secret_list = map(retrieveValue,ids)
    secret_dict = dict(ChainMap(*secret_list))
    file_loader = FileSystemLoader(json_path)
    env         = Environment(loader=file_loader)
    template    = env.get_template(head_file)
    head        = template.render(azurekv=secret_dict)
    return (head)

def retrieveValue(secret_id):
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

def main():
    with open(json_path + base_file) as json_file:
        base = json.load(json_file)

    try: 
        head = renderTemplate(vault_url)
        head_json_output = json.loads(head)
    except Exception as e:  # find real exception type 
        print("Output template does not render as json: ", e)
        return 

    with open(json_path + appsettings_json, 'w') as outfile:
        merged_appsettings_data = merge_head_to_base(base, head_json_output)
        json.dump(merged_appsettings_data, outfile)

if __name__ == '__main__':
    main()