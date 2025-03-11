from fastapi import FastAPI, HTTPException, Query
import requests
from io import BytesIO
from PIL import Image, ImageSequence
import logging

app = FastAPI()

# Configuração do logger para debug no Railway
logging.basicConfig(level=logging.INFO)

@app.get("/imagetotable/imageurl")
def image_to_table(image_url: str, resolution: float = Query(1.0, gt=0, le=1.0)):
    try:
        logging.info(f"Recebendo imagem de: {image_url}")

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        frames = {}
        width, height = image.size

        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")

            new_width = max(1, int(width * resolution))
            new_height = max(1, int(height * resolution))

            # Pillow compatível com versões antigas
            try:
                frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                frame = frame.resize((new_width, new_height), Image.LANCZOS)

            pixels = []

            for y in range(new_height):
                for x in range(new_width):
                    r, g, b, a = frame.getpixel((x, y))
                    roblox_alpha = round(1 - (a / 255), 2)
                    roblox_alpha = int(roblox_alpha) if roblox_alpha == 0 else roblox_alpha
                    
                    if roblox_alpha < 1:
                        pixels.append(f"{x},{y},{r},{g},{b},{roblox_alpha}")

            if pixels:
                frames[f"Frame {i+1}"] = pixels

        if not frames:
            return {"message": "A imagem não possui pixels visíveis."}

        return {"width": new_width, "height": new_height, **frames}

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar a imagem: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")

    except Exception as e:
        logging.error(f"Erro ao processar a imagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
