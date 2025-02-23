from fastapi import FastAPI, HTTPException
import requests
from io import BytesIO
from PIL import Image, ImageSequence
import base64
import json

app = FastAPI()

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@app.get("/imagetotable/imageurl")
def image_to_table(image_url: str):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        frames = []
        
        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")
            width, height = frame.size
            pixels = [
                (frame.getpixel((x, y))[:3] + (frame.getpixel((x, y))[3],))
                for y in range(height)
                for x in range(width)
            ]
            
            compressed_pixels = base64.b64encode(json.dumps(pixels).encode()).decode()
            frames.append({
                f"Frame {i+1}": {
                    "source": encode_image(frame),
                    "width": width,
                    "height": height,
                    "pixels": compressed_pixels
                }
            })
        
        return {"frames": frames} if len(frames) > 1 else frames[0]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
