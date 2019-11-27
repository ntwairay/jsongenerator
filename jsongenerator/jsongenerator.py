import os, uuid, json, re
from jsonmerge import merge, Merger
from azure.keyvault import KeyVaultClient
from azure.common.credentials import ServicePrincipalCredentials

# Environment variable
# vault_url must be in the format 'https://<vaultname>.vault.azure.net'
azure_client_id    =os.environ['AZURE_CLIENT_ID']
azure_client_secret=os.environ['AZURE_CLIENT_SECRET']
azure_tenant_id    =os.environ['AZURE_TENANT_ID']
vault_url          =os.environ['AZURE_KEY_VAULT_URL']

# Setup Azure service principle 
credentials = ServicePrincipalCredentials(
    client_id=azure_client_id,
    secret   =azure_client_secret,
    tenant   =azure_tenant_id
)
# create Azure Client
client = KeyVaultClient(credentials)

def replace_value(pointer, bottom_key, secret_value):
    try:
        if bottom_key not in pointer:
            print('Failed to replace key "{key}"'.format(key=bottom_key))        
        else:
            print('Replacing key "{key}"'.format(key=bottom_key))    
            pointer[bottom_key] = secret_value
    except KeyError:
        print('Failed to replace delimited_key "{key}"'.format(key=bottom_key))
    return pointer  

def getPointer(appsettings_data, key):
    pointer = appsettings_data
    return pointer[key]
  
def retrieveValue(appsettings_data,secret_id):
    regex = re.compile(vault_url + 'secrets/(.*)', re.IGNORECASE)
    match = regex.search(secret_id)
    assert match, 'Failed to parse the secret name from "{id}"'.format(id=id)
    secret_name   = match.group(1)
    secret_bundle = client.get_secret(vault_url, secret_name, "")
    secret_value  = secret_bundle.value
    DELIMITER = '--'
    keys      = secret_name.split(DELIMITER)
    pointer   = [getPointer(appsettings_data,key) for key in keys[:-1]]
    replace_value(pointer[0],keys[-1],secret_value)

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
    secrets = client.get_secrets(vault_url)
    ids = [secret.as_dict()['id'] for secret in secrets]

    base_path = './jsongenerator/json/base.json'
    head_path = './jsongenerator/json/head.json'

    with open(base_path) as json_file:
        base = json.load(json_file)

    with open(head_path) as json_file:
        head = json.load(json_file)

    with open('result.json', 'w') as outfile:
        merged_appsettings_data = merge_head_to_base(base, head)
        # inject azure key vault secret
        [retrieveValue(merged_appsettings_data, id) for id in ids]
        json.dump(merged_appsettings_data, outfile)

if __name__ == '__main__':
    main()