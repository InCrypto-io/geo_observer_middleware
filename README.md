# GEO OBSERVER MIDDLEWARE

# Prepare config for docker or standalone launch
Copy and rename `config.example.py` to `config.py`.<br />
`WEB3_PROVIDER` - web socket URL address to Ethereum<br /> 
`Voting_Address` - address of Voting contract<br /> 
`VOTING_CREATED_AT_BLOCK` - number of block, where contract deployed, event will be collect from this block<br /> 
`GEOToken_Address` - address of a GEOToken contract<br /> 
`MNEMONIC` - 12 words for restoring private key<br /> 
`DB_URL` - URL for mongo db, by default prepared to docker configuration<br /> 
`CONFIRMATION_COUNT` - the number of blocks, after which it is believed that the chain will not split<br /> 
`INTERVAL_OF_EPOCH` - interval for saving preprocessed state of contract to db<br /> 
`VOTES_ROUND_TO_NUMBER_OF_DIGIT` - the number of real digits to which the fractional part of tokens is rounded<br /> 
`REST_API_PORT` - port where REST API listening of requests, 
if you want change it, make it and in `docker-compose.yaml` file<br /> 

# With Docker
### Requirement
    docker
    docker-compose    

#### Launch REST API Server
`docker-compose build && docker-compose up`

#### Clean
`docker-compose down` <br />
`docker-compose rm`

# Standalone
### Requirement
Install python 3, mongodb<br />
`pip install -r requirements.txt`

## Prepare config
Change in config file URL to mongo db server <br />
`DB_URL = "mongodb://127.0.0.1:27017/"`

#### Launch REST API Server
 `python3 ./src/manage.py`

#### Clean
 `python3 ./src/manage.py CLEAN`

# Usage
 Watch https://documenter.getpostman.com/view/5899787/S1a1ZoML
