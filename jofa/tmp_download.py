import requests
import os

hero_images = [
    'https://images.unsplash.com/photo-1556228578-8d85ec019d14?w=1000'
]

headers = {'User-Agent': 'Mozilla/5.0'}

for i, url in enumerate(hero_images):
    print(f"Downloading {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            with open(f"hero_1.jpg", "wb") as f:
                f.write(r.content)
            print(f"Success hero_1.jpg")
        else:
            print(f"Failed {r.status_code}")
    except Exception as e:
        print(f"Error {e}")
