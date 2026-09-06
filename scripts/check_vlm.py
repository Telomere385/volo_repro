"""Real image request. Config loaded by calling shell; never prints credentials."""
import argparse, base64, json, os
from pathlib import Path
from openai import OpenAI
p=argparse.ArgumentParser()
p.add_argument("image",type=Path)
a=p.parse_args()
image=a.image.read_bytes()
mime="image/png" if image[:4] == bytes([137, 80, 78, 71]) else "image/jpeg"
client=OpenAI(base_url=os.environ["VLM_BASE_URL"],api_key=os.environ["VLM_API_KEY"],timeout=90,max_retries=0)
result=client.chat.completions.create(model=os.environ["VLM_MODEL"],max_tokens=1024,temperature=0,
    messages=[{"role":"user","content":[{"type":"text","text":
    'Describe this robot scene briefly. Return only JSON with an "objects" array of object names and a "description" string of at most two sentences.'},
    {"type":"image_url","image_url":{"url":"data:"+mime+";base64,"+base64.b64encode(image).decode()}}]}])
content=result.choices[0].message.content or ""
print(content)
print("FINISH_REASON", result.choices[0].finish_reason)
if result.choices[0].finish_reason == "length":
    raise RuntimeError("VLM response was truncated by the output token limit")
raw=content.strip()
if raw.startswith("```"):
    raw="\n".join(raw.splitlines()[1:-1])
data=json.loads(raw)
assert isinstance(data["objects"],list) and isinstance(data["description"],str)
print("VISION_API_OK")
