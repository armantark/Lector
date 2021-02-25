import json
import sys
import os


class Config:
    filename = 'config.json'
    
    prefix = os.environ['prefix']
    token = os.environ['token']

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        del data

    except FileNotFoundError:
        print(f'\'{filename}\' does not exist.')
        sys.exit()

    except json.decoder.JSONDecodeError:
        print(f'\'{filename}\' is malformed.')
        sys.exit()

    except KeyError:
        print(f'\'{filename}\' is missing information.')
        sys.exit()