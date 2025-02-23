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
                    roblox_alpha = round(1 - (a / 255), 2)
                    roblox_alpha = int(roblox_alpha) if roblox_alpha == 0 else roblox_alpha
                    
                    if roblox_alpha < 1:
                        pixels.append(f"{x} {y} {r} {g} {b} {roblox_alpha}")

            if pixels:
                frames[f"Frame {i+1}"] = " ".join(pixels)  

        return frames if frames else {"message": "A imagem não possui pixels visíveis."}
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
