from fastapi import FastAPI, HTTPException
import requests
from io import BytesIO
from PIL import Image, ImageSequence

app = FastAPI()

@app.get("/imagetotable/imageurl")
def image_to_table(image_url: str):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        frames = {}

        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")
            width, height = frame.size
            pixels = []

            for y in range(height):
                for x in range(width):
                    r, g, b, a = frame.getpixel((x, y))
                    pixels.append([x, y, r, g, b, round(a / 255, 2)])  # Normaliza transparência para 0-1

            frames[f"Frame {i+1}"] = pixels  # Lista compactada dos pixels

        return frames
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
