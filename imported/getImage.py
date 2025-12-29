import requests
import json
import time


key = "c71e2ce0a9ddc33eb8468f83f3667dd0"
def create_image_task(prompt):
    url = "https://api.kie.ai/api/v1/jobs/createTask"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    payload = {
        "model": "google/nano-banana",
        "input": {
            "prompt": prompt,
            "output_format": "png",
            "image_size": "1:1"
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    return result['data']['taskId']

def get_task_info(id_):
    url = "https://api.kie.ai/api/v1/jobs/recordInfo"
    params = {"taskId": id_}
    headers = {"Authorization": f"Bearer {key}"}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    return result



def getImage(prompt):
    id_ = create_image_task(prompt)
    print(f"Created image task with ID: {id_}")
    while True:
        time.sleep(5)
        r = get_task_info(id_)
        if r['data']['state'] == 'success':
            return json.loads(r["data"]["resultJson"])['resultUrls'][0]
        


prompt = "Recreate a pixel-art scene of a lone armored knight taking shelter inside a small rocky cave during a heavy rainstorm. Maintain nano-level precision in rendering the knight’s silver plate armor, red cape, and hunched, contemplative posture as he sits beside a small campfire. Preserve intelligent context awareness for the emotional tone—melancholic, reflective, and weary. Keep the fire’s warm orange glow illuminating the knight and the cave interior with molecular-scale accuracy, contrasting against the cold, rain-soaked landscape outside. Show raindrops falling in long streaks, dark storm clouds overhead, and a distant horizon tinted with faint sunset reds. Include the knight’s sword lying on the ground outside the cave, slightly wet from the rain, ensuring smart texture preservation of metal reflections and ground moisture. Maintain pixel-art style integrity with ultra-sharp micro-details, atmosphere consistency, and lighting coherence. Aim for emotional depth, environmental realism, and nano-scale artistic fidelity throughout the entire scene."

image = getImage(prompt)
print(image)