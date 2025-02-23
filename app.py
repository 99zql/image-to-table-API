from fastapi import FastAPI, HTTPException, Query
import requests
from io import BytesIO
from PIL import Image, ImageSequence

app = FastAPI()

@app.get("/imagetotable/imageurl")
def image_to_table(image_url: str, resolution: float = Query(1.0, gt=0, le=1.0)):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        frames = {}

        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")
            width, height = frame.size
            
            # Redimensionar a imagem de acordo com a resolução fornecida
            new_width = max(1, int(width * resolution))
            new_height = max(1, int(height * resolution))
            frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            pixels = []

            for y in range(new_height):
                for x in range(new_width):
                    r, g, b, a = frame.getpixel((x, y))
                    roblox_alpha = round(1 - (a / 255), 2)  # Mantém transparência sem 0.0
                    roblox_alpha = int(roblox_alpha) if roblox_alpha == 0 else roblox_alpha
                    
                    if roblox_alpha < 1:  # Apenas pixels visíveis no Roblox
                        pixels.append(f"{x},{y},{r},{g},{b},{roblox_alpha}")

            if pixels:  # Apenas adiciona frames que possuem pixels visíveis
                frames[f"Frame {i+1}"] = {
                    "width": new_width,
                    "height": new_height,
                    "pixels": ",".join(pixels)
                }

        return frames if frames else {"message": "A imagem não possui pixels visíveis."}
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
