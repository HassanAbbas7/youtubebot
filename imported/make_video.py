import requests
import json
import time 

key = "c71e2ce0a9ddc33eb8468f83f3667dd0"

def create_video_task(prompt, image_url):
    url = "https://api.kie.ai/api/v1/jobs/createTask"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    payload = {
        # "model": "kling/v2-5-turbo-image-to-video-pro",
        "model": "grok-imagine/image-to-video",
        "input": {
            "image_url": image_url,
            "tail_image_url": image_url,
            "duration": "5",
            "negative_prompt": "blur, distort, and low quality",
            "cfg_scale": 0.8
        }
    }
    if prompt:
        payload["input"]["prompt"] = prompt
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    print(result)
    return result['data']['taskId']


def get_video_task_info(id_):
    url = "https://api.kie.ai/api/v1/jobs/recordInfo"
    params = {"taskId": id_}
    headers = {"Authorization": f"Bearer {key}"}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    return result

def getVideo(prompt, image_url):
    id_ = create_video_task(prompt, image_url)
    print(f"Created video task with ID: {id_}")
    while True:
        time.sleep(5)
        r = get_video_task_info(id_)
        if r['data']['state'] == 'success':
            return json.loads(r["data"]["resultJson"])['resultUrls'][0]


# create_video_task("Unmoving composition focused on the breathing neon signs transitioning through warm hues, raindrops trickling vertically down the window in sharp focus. Behind the water trails, distant city lights glow diffusely while condensation slowly forms and drips down a glass on the table, plant leaves quivering minimally in the still air.", "https://tempfile.aiquickdraw.com/workers/nano/image_1764785589353_6qrr2e_1x1_1024x1024.png")


video = getVideo('''Create a cinematic pixel-art animation based on a lone armored knight resting inside a cave during a stormy evening. Maintain nano-level precision for the knight’s armor reflections, red cape, and weary posture. Animate the campfire with soft, looping flames and gentle, glowing embers rising upward. Preserve intelligent context awareness of lighting: warm firelight flickering across the knight’s armor and the cave walls, with subtle nano-scale shading variations.

Outside the cave, animate the rain as long streaks falling at a steady pace, with molecular-accurate splash effects on the ground. Add slow movement to the storm clouds, giving the sky a dynamic, brooding atmosphere. Keep the distant horizon’s faint red glow consistent as the storm shifts. Introduce tiny environmental motions: grass trembling in the wind, the sword outside catching occasional glints from lightning-illuminated clouds.

Ensure the overall mood remains somber, reflective, and immersive with pixel-perfect temporal consistency.''',"https://tempfile.aiquickdraw.com/workers/nano/image_1765372226428_s7ycum_1x1_1024x1024.png")
print(video)

# print(get_video_task_info("fb55ab1c06d48121e1a60aaf74bc864d"))