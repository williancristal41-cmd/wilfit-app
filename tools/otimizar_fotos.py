"""Gera versões leves das fotos dos exercícios (bucket 'fotos' do Supabase).
img/p/<nome>.webp  -> miniatura 128x128 (listas)
img/m/<nome>.webp  -> média, até 900 px de largura (detalhe do exercício)
img/fotos.json     -> índice usado pelo app (arquivo original -> versão leve)
Só reprocessa fotos novas ou alteradas."""
import io, json, os, urllib.request, urllib.parse
from PIL import Image, ImageOps

URL = "https://hvbtrknxhxtulnlcymoh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2YnRya254aHh0dWxubGN5bW9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ1MTAwMDIsImV4cCI6MjExMDA4NjAwMn0.9hJ7cZ7hutNgTv4vlpwzg5Nk0i6xlHWDVuQ69AmZgvU"  # chave pública (anon), a mesma usada no app
H = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}

def listar(prefixo=""):
    req = urllib.request.Request(URL + "/storage/v1/object/list/fotos", method="POST", headers=H,
        data=json.dumps({"prefix": prefixo, "limit": 1000, "offset": 0, "sortBy": {"column": "name", "order": "asc"}}).encode())
    itens = json.load(urllib.request.urlopen(req, timeout=60))
    for o in itens:
        caminho = (prefixo + "/" if prefixo else "") + o["name"]
        if o.get("id") is None:
            yield from listar(caminho)
        elif o["name"].lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            yield caminho, o.get("updated_at") or o.get("created_at") or ""

os.makedirs("img/p", exist_ok=True); os.makedirs("img/m", exist_ok=True)
try:
    antigo = json.load(open("img/fotos.json", encoding="utf-8"))
except Exception:
    antigo = {"arquivos": {}, "versoes": {}}
arquivos, versoes, feitos = {}, {}, 0
for caminho, ver in listar():
    nome = os.path.splitext(caminho.replace("/", "__"))[0]
    nome = "".join(c if c.isalnum() or c in "-_" else "_" for c in nome)
    arquivos[caminho] = nome; versoes[caminho] = ver
    if antigo.get("versoes", {}).get(caminho) == ver and os.path.exists(f"img/p/{nome}.webp") and os.path.exists(f"img/m/{nome}.webp"):
        continue
    dado = urllib.request.urlopen(URL + "/storage/v1/object/public/fotos/" + urllib.parse.quote(caminho), timeout=120).read()
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(dado))).convert("RGB")
    ImageOps.fit(im, (128, 128), Image.LANCZOS).save(f"img/p/{nome}.webp", "WEBP", quality=72, method=6)
    m = im.copy(); m.thumbnail((900, 900), Image.LANCZOS); m.save(f"img/m/{nome}.webp", "WEBP", quality=78, method=6)
    feitos += 1
for f in os.listdir("img/p"):
    if f[:-5] not in arquivos.values():
        os.remove("img/p/" + f); os.path.exists("img/m/" + f) and os.remove("img/m/" + f)
json.dump({"arquivos": arquivos, "versoes": versoes}, open("img/fotos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
print(f"{len(arquivos)} fotos no índice, {feitos} processadas agora")
