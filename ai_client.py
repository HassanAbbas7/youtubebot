import requests
from config import AI_PROMPT_ENDPOINT, AI_IMAGE_ENDPOINT, AI_API_KEY, TESTING, KIE_API_KEY, TESTING, SET_TAIL_IMAGE
from typing import Tuple
import base64
import os
import json

import time

HEADERS = {"Authorization": f"Bearer {AI_API_KEY}"} if AI_API_KEY else {}


def generate_prompt(title: str, prompt_template: str) -> str:
    if TESTING:
        return "A person walking through a bunch of daffodils"
    
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {AI_API_KEY}",
    },
    data=json.dumps({
        "model": "tngtech/deepseek-r1t2-chimera:free",
        "messages": [
        {
            "role": "user",
            "content": f"Give a SINGLE, very detailed prompt for generating a lofi-style relaxing image with relaxing and cozy vibe and some potentially animatable elements. The prompt should be an altered version of a base prompt. It should be altered depending on the title.(just give the prompt and nothing else):\nTitle:{title}\nBase prompt:\"{prompt_template}\""
        }
        ]
    })
    )
    return response.json()["choices"][0]["message"]["content"]


def create_image_task(prompt):
    url = "https://api.kie.ai/api/v1/jobs/createTask"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIE_API_KEY}"
    }

    payload = {
        "model": "google/nano-banana",
        "input": {
            "prompt": prompt,
            "output_format": "png",
            "image_size": "16:9"
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    return result['data']['taskId']

def get_task_info(id_):
    url = "https://api.kie.ai/api/v1/jobs/recordInfo"
    params = {"taskId": id_}
    headers = {"Authorization": f"Bearer {KIE_API_KEY}"}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    return result



def generate_image(prompt):
    if TESTING:
        return "https://images.unsplash.com/photo-1761839258605-d1b118266ccc?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    id_ = create_image_task(prompt)
    print(f"Created image task with ID: {id_}")
    while True:
        time.sleep(5)
        r = get_task_info(id_)
        if r['data']['state'] == 'success':
            return json.loads(r["data"]["resultJson"])['resultUrls'][0]
        
def create_video_task(prompt, image_url):
    url = "https://api.kie.ai/api/v1/jobs/createTask"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIE_API_KEY}"
    }

    payload = {
        "model": "kling/v2-5-turbo-image-to-video-pro",
        "input": {
            "prompt": prompt,
            "image_url": image_url,
            # "tail_image_url": image_url,
            "duration": "5",
            "negative_prompt": "blur, distort, and low quality",
            "cfg_scale": 0.5,
            "aspect_ratio": "16:9"

        }
    }

    if SET_TAIL_IMAGE:
        payload["input"]["tail_image_url"] = image_url

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    return result['data']['taskId']

def get_prompt_for_video(image: str) -> str:
    if TESTING:
        return "A peaceful, lofi-inspired ambience with mildly animated elements like gently swaying trees and floating lanterns."
    


    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I intend to use an image to video model to create a relaxing lofi-style ambience video. Provide a SINGLE, very detailed prompt for generating such a video with relaxing and cozy vibe and some mildly animated elements based on what you see in this image I sent you. Make sure all the elements are subtly animated. Give only prompt, no other text. Also, the model tends to ignore outdoor elements, make sure they are animated properly." 
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image
                    }
                }
            ]
        }
    ]
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=payload)
    
    print(response.json())
    return response.json()["choices"][0]["message"]["content"]
# def get_video_task_info(id_):
#     url = "https://api.kie.ai/api/v1/jobs/recordInfo"
#     params = {"taskId": id_}
#     headers = {"Authorization": f"Bearer {key}"}

#     response = requests.get(url, headers=headers, params=params)
#     result = response.json()
#     return result

def getVideo(prompt, image_url):
    id_ = create_video_task(prompt, image_url)
    print(f"Created video task with ID: {id_}")
    while True:
        time.sleep(5)
        r = get_task_info(id_)
        if r['data']['state'] == 'success':
            return json.loads(r["data"]["resultJson"])['resultUrls'][0]



if __name__ == "__main__":
    image = "https://images.unsplash.com/photo-1764377848067-aefbce306f80?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    prompt = get_prompt_for_video(image)
    print("Generated video prompt:", prompt)