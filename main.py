from fastapi import FastAPI, HTTPException, Query
import requests
from io import BytesIO
from PIL import Image, ImageSequence
import threading
import time
import os
from datetime import datetime

app = FastAPI(title="Roblox Image Converter API", version="1.0.0")

# Variáveis globais para controle do keep-alive
KEEP_ALIVE_ENABLED = True
KEEP_ALIVE_INTERVAL = 25 * 60  # 25 minutos em segundos

def keep_alive_ping():
    """Função que mantém o serviço ativo fazendo requisições para si mesmo"""
    base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
    
    while KEEP_ALIVE_ENABLED:
        try:
            time.sleep(KEEP_ALIVE_INTERVAL)
            
            # Faz uma requisição simples para o health check
            response = requests.get(f"{base_url}/health", timeout=10)
            print(f"[{datetime.now()}] Keep-alive ping: {response.status_code}")
            
        except Exception as e:
            print(f"[{datetime.now()}] Erro no keep-alive: {e}")

# Inicia a thread de keep-alive quando o app inicializa
@app.on_event("startup")
def startup_event():
    if os.getenv("RENDER_EXTERNAL_URL"):  # Só ativa no Render
        threading.Thread(target=keep_alive_ping, daemon=True).start()
        print("Keep-alive iniciado para Render")

@app.get("/")
def read_root():
    return {
        "message": "Roblox Image Converter API",
        "endpoints": {
            "/imageapi": "Converte imagem para formato Roblox",
            "/health": "Health check",
            "/docs": "Documentação da API"
        },
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """Endpoint para verificação de saúde do serviço"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.get("/imageapi")
def image_to_table(imageurl: str, resolution: float = Query(1.0, gt=0, le=10.0)):
    """
    Converte uma imagem em dados de pixel para uso no Roblox
    
    Args:
        imageurl: URL da imagem para converter
        resolution: Escala da resolução (0.1 a 10.0)
    
    Returns:
        Dict com dados dos pixels organizados por frame
    """
    try:
        # Download da imagem com headers para evitar bloqueios
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(imageurl, timeout=15, headers=headers)
        response.raise_for_status()
        
        # Validação do tipo de arquivo
        content_type = response.headers.get('content-type', '').lower()
        if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
            raise HTTPException(status_code=400, detail="URL não contém uma imagem válida")

        image = Image.open(BytesIO(response.content))
        frames = {}
        width, height = image.size
        
        # Validação de tamanho da imagem
        if width > 2000 or height > 2000:
            raise HTTPException(status_code=400, detail="Imagem muito grande (máximo 2000x2000)")

        frame_count = 0
        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame_count += 1
            
            # Limite de frames para evitar sobrecarga
            if frame_count > 100:
                break
                
            frame = frame.convert("RGBA")

            new_width = max(1, int(width * resolution))
            new_height = max(1, int(height * resolution))
            frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

            pixels = []
            for y in range(new_height):
                for x in range(new_width):
                    r, g, b, a = frame.getpixel((x, y))
                    
                    # Pula pixels transparentes
                    if a == 0:
                        continue
                    
                    transparency = round(1 - (a / 255), 2)
                    pixels.append(f"{x},{y},{r},{g},{b},{transparency}")

            if pixels:
                frames[f"Frame {i+1}"] = ",".join(pixels)

        if not frames:
            return {"message": "A imagem não possui pixels visíveis."}

        return {
            "width": new_width, 
            "height": new_height, 
            "total_frames": len(frames),
            "original_size": f"{width}x{height}",
            **frames
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Timeout ao baixar a imagem")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {str(e)}")
    except Image.UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint adicional para controlar o keep-alive
@app.post("/keep-alive/toggle")
def toggle_keep_alive(enabled: bool = Query(True)):
    """Ativar/desativar o keep-alive (apenas para debug)"""
    global KEEP_ALIVE_ENABLED
    KEEP_ALIVE_ENABLED = enabled
    return {"keep_alive_enabled": KEEP_ALIVE_ENABLED}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
