import time
import jwt

# ak = "AkNdD89nLyPhEkJrFLC8MeG83CrLaJmY"
# sk = "yMLCNFFRYkQeCnkH93dgnNNENyFrgtkk"

def encode_jwt_token(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800, # The valid time, in this example, represents the current time+1800s(30min)
        "nbf": int(time.time()) - 5 # The time when it starts to take effect, in this example, represents the current time minus 5s
    }
    token = jwt.encode(payload, sk, headers=headers)
    return token

