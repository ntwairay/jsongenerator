import os, json, re, jinja2
from jsonmerge import merge, Merger
from azure.keyvault import KeyVaultClient
from jinja2 import Environment, FileSystemLoader
from collections import ChainMap
from azure.common.credentials import ServicePrincipalCredentials

# Environment variable
# vault_url must be in the format 'https://<vaultname>.vault.azure.net'
vault_url          = os.environ['AZURE_KEY_VAULT_URL']
environment        = os.environ['PIPELINE_ENVIRONMENT']
azure_client_id    = os.environ['AZURE_CLIENT_ID']
azure_client_secret= os.environ['AZURE_CLIENT_SECRET']
azure_tenant_id    = os.environ['AZURE_TENANT_ID']

# Setup Azure client
credentials = ServicePrincipalCredentials(
    client_id = azure_client_id,
    secret    = azure_client_secret,
    tenant    = azure_tenant_id
)

# Setup Azure client
client = KeyVaultClient(credentials)

# Base and environment json path
json_path = './json/'
base_file = 'base.json'
head_file = 'head.json'
appsettings_json = 'appsettings-'+environment +'.json'

def renderTemplate(vault_url):
    secrets = client.get_secrets(vault_url)
    ids     = [secret.as_dict()['id'] for secret in secrets]
    secret_list = map(retrieveValue,ids)
    secret_dict = dict(ChainMap(*secret_list))
    file_loader = FileSystemLoader(json_path)
    env         = Environment(loader=file_loader, undefined=jinja2.StrictUndefined)
    template    = env.get_template(head_file)
    head        = template.render(azurekv=secret_dict, environment=environment)
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
        json.dump(merged_appsettings_data, outfile, sort_keys=True)    


if __name__ == '__main__':
    main()