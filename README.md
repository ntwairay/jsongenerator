## Repository 
This repository is to configure a customise format appsettings.json using json merge and azure key vault

## Environment variables for Azure devops pipeline

- AZURE_SUBSCRIPTION_ID
- AZURE_KEY_VAULT_URL  
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
- AZURE_TENANT_ID
- PIPELINE_ENVIRONMENT
- AZURE_STORAGE_CONNECTION_STRING

## Run on local machine

- virtualenv venv
- source venv/bin/activate
- pip install -r requirements.txt
- export environment variables
- download the current appsetting json from Azure storage
 (az storage blob download -c $PIPELINE_ENVIRONMENT -n appsettings-$PIPELINE_ENVIRONMENT.json -f ./json/appsettings-current.json)

## Execute python scripts

- python ./src/jsongenerator.py (***Generate appsettings.json***)
- python ./src/jsondiff.py  (***Check the differences between two json files***)
