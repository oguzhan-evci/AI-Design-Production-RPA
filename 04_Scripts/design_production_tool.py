from rembg import remove, new_session
from PIL import Image
import io
import os

# --- 1. MODEL HAZIRLIĞI (Global Scope) ---
# Bu bölüm dışarıda kalır; model RAM'de açık kalır ve her seferinde yüklenmez.
model_otunumu = new_session("birefnet-general")

# Klasör yolları global alanda tanımlandı (Değişmedi)
klasor_ham = "04-Optimize-Process" 
klasor_final = "05-Final-Process"  

def akilli_arka_plan_silici(input_path, output_path):
    """Yapay zeka kullanarak arka planı temizler."""
    with open(input_path, 'rb') as f:
        ham_veri = f.read()

    img_temp = Image.open(io.BytesIO(ham_veri))
    if img_temp.width > 2500 or img_temp.height > 2500:
        img_temp.thumbnail((2500, 2500), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img_temp.save(buffer, format="PNG")
        ham_veri = buffer.getvalue()

    temiz_veri = remove(ham_veri, session=model_otunumu, alpha_matting=False)
    sonuc_resim = Image.open(io.BytesIO(temiz_veri)).convert("RGBA")
    sonuc_resim.save(output_path)

def baskiya_hazirla_v2(giris_dosyasi, cikis_dosyasi):
    """Resmi POD standartlarına (4500x5400, 300 DPI) getirir."""
    CANVAS_GENISLIK = 4500
    CANVAS_YUKSEKLIK = 5400
    DPI_AYARI = (300, 300) 
    UST_BOSLUK = 300 
    ALT_BOSLUK = 100 
    MAX_RESIM_YUKSEKLIGI = CANVAS_YUKSEKLIK - UST_BOSLUK - ALT_BOSLUK

    img = Image.open(giris_dosyasi).convert("RGBA")
    hedef_genislik_limit = int(CANVAS_GENISLIK * 0.85)
    oran_genislik = hedef_genislik_limit / img.width
    oran_yukseklik = MAX_RESIM_YUKSEKLIGI / img.height
    final_oran = min(oran_genislik, oran_yukseklik)
    
    yeni_genislik = int(img.width * final_oran)
    yeni_yukseklik = int(img.height * final_oran)

    img_yeni = img.resize((yeni_genislik, yeni_yukseklik), Image.Resampling.LANCZOS)
    final_canvas = Image.new("RGBA", (CANVAS_GENISLIK, CANVAS_YUKSEKLIK), (0, 0, 0, 0))
    pos_x = (CANVAS_GENISLIK - img_yeni.width) // 2
    pos_y = UST_BOSLUK 
    final_canvas.paste(img_yeni, (pos_x, pos_y), img_yeni)
    final_canvas.save(cikis_dosyasi, dpi=DPI_AYARI)

# --- 2. ANA ORKESTRA FONKSİYONU (YENİ EKLENEN KISIM) ---

def tasarimi_isleme_sok(seo_ismi):
    """UiPath tarafından çağrılacak ana giriş kapısı."""
    try:
        # Uzantı temizleme işlemi (Bozulmadı, sadece fonksiyon içine alındı)
        temiz_isim = seo_ismi.replace(".png", "")
        
        girdi = os.path.join(klasor_ham, f"{temiz_isim}.png")
        ara_dosya = os.path.join(klasor_final, f"{temiz_isim}_temp_seffaf.png")
        cikti = os.path.join(klasor_final, f"{temiz_isim}-design.png")

        if not os.path.exists(girdi):
            return "FAILED" # UiPath bunu 'Hatalı' olarak Excel'e yazacak

        # Çekirdek işlemler tetikleniyor (Logic bozulmadı)
        akilli_arka_plan_silici(girdi, ara_dosya)
        baskiya_hazirla_v2(ara_dosya, cikti)
        
        if os.path.exists(ara_dosya):
            os.remove(ara_dosya)
            
        return "SUCCESS" # UiPath bunu 'Done' olarak Excel'e yazacak

    except Exception:
        return "FAILED" # Herhangi bir teknik hata durumunda FAILED döner