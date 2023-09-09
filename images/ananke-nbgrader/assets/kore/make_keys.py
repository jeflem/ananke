# create new key pair for LTI communication

import json

from Crypto.PublicKey import RSA
from jwcrypto.jwk import JWK

key_dir = 'keys'
key_name = 'lti_key'

# create key pair
key = RSA.generate(4096)
private_key = key.exportKey()
public_key = key.publickey().exportKey()

# write private key to file
with open(f'{key_dir}/{key_name}', 'wb') as f:
    f.write(private_key)

# write public key
with open(f'{key_dir}/{key_name}.pub', 'wb') as f:
    f.write(public_key)

# make key set
jwk_obj = JWK.from_pem(public_key)
public_jwk = json.loads(jwk_obj.export_public())
public_jwk['alg'] = 'RS256'
public_jwk['use'] = 'sig'
public_jwk_str = json.dumps(public_jwk)

# write key set
with open(f'{key_dir}/{key_name}.json', 'w') as f:
    f.write(public_jwk_str)
