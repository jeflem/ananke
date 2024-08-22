# Used to create new key pair for LTI communication.

import json

from Crypto.PublicKey import RSA
from jwcrypto.jwk import JWK

key_dir = '/opt/kore/keys'
key_name = 'lti_key'

# Create key pair.
key = RSA.generate(4096)
private_key = key.exportKey()
public_key = key.publickey().exportKey()

# Write private key to file.
with open(f'{key_dir}/{key_name}', 'wb') as f:
    f.write(private_key)

# Write public key.
with open(f'{key_dir}/{key_name}.pub', 'wb') as f:
    f.write(public_key)

# Make key set.
jwk_obj = JWK.from_pem(public_key)
public_jwk = json.loads(jwk_obj.export_public())
public_jwk['alg'] = 'RS256'
public_jwk['use'] = 'sig'
public_jwk_str = json.dumps(public_jwk)

# Write key set.
with open(f'{key_dir}/{key_name}.json', 'w') as f:
    f.write(public_jwk_str)
