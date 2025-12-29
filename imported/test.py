import requests
import time
from getJWT import encode_jwt_token

api_key = encode_jwt_token("ArJMNNJdytAgEg3KHERkrd3LKbtnRdCB", "AnmeKLHaRMMFneJ3ftYGtFnhMRNgrBNn")
base_url = "https://api-singapore.klingai.com"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

data = {
    "model_name": "kling-v1",
    "prompt": "a futuristic city floating above the clouds"
}

r = requests.post(f"{base_url}/v1/images/generations", json=data, headers=headers)
print(r.json())
task_id = r.json()["data"]["task_id"]

while True:
    q = requests.get(f"{base_url}/v1/images/generations/{task_id}", headers=headers)
    result = q.json()
    print(result)
    if result["data"]["task_status"] == "succeed":
        print(result["data"]["task_result"]["images"])
        break
    if result["data"]["task_status"] == "failed":
        print("failed")
        break
    time.sleep(1)
