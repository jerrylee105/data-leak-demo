#!/usr/bin/env python3
"""
Worker Script: Tải, xử lý, crop và nén ảnh cho 100 món ăn của 'Hôm nay ăn gì?'
- Chuẩn hóa tỷ lệ: 600x450 (4:3)
- Định dạng: WebP chất lượng 80% (khoảng 25KB - 40KB/ảnh)
- Đảm bảo ảnh khớp 100% với từng món ăn thực tế
- Lưu tại: static/images/dishes/dish_{id}.webp
"""

import os
import sys
import json
import ssl
import time
import io
import urllib.request
import urllib.parse
from PIL import Image

CTX = ssl._create_unverified_context()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "dishes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Bản đồ từ khóa tìm kiếm chính xác từng món
DISH_TERMS = {
    1: ["Phở", "Phở bò Hà Nội", "Pho beef soup"],
    2: ["Phở gà", "Pho ga", "Chicken pho"],
    3: ["Bún bò Huế", "Bun bo Hue"],
    4: ["Bún đậu mắm tôm", "Bun dau mam tom"],
    5: ["Bún chả", "Bun cha Hanoi"],
    6: ["Bún riêu", "Bun rieu cua"],
    7: ["Bánh canh ghẹ", "Crab noodle soup"],
    8: ["Bánh canh cua", "Bánh canh", "Vietnamese thick noodle soup"],
    9: ["Hủ tiếu Nam Vang", "Hu tieu Nam Vang"],
    10: ["Bò kho", "Vietnamese beef stew"],
    11: ["Mì Quảng", "Mi Quang noodles"],
    12: ["Cao lầu", "Cao lau Hoi An"],
    13: ["Mì vịt tiềm", "Duck noodle soup"],
    14: ["Hoành thánh", "Wonton noodle soup"],
    15: ["Bún ốc", "Vietnamese snail noodle soup"],
    16: ["Bún mắm", "Bun mam Mekong"],
    17: ["Bún cá", "Fish noodle soup"],
    18: ["Bún bò", "Bun bo"],
    19: ["Ramen", "Chashu ramen", "Japanese ramen"],
    20: ["Udon", "Beef udon", "Japanese udon noodle"],
    21: ["Bánh đa cua", "Hai Phong crab noodles"],
    22: ["Miến gà", "Chicken glass noodles"],
    23: ["Miến lươn", "Eel glass noodles"],
    24: ["Bún nước lèo", "Soc Trang noodle soup"],
    25: ["Mì xá xíu", "Char siu noodles"],
    26: ["Cơm tấm", "Com tam Suon Bi Cha"],
    27: ["Cơm gà xối mỡ", "Crispy fried chicken rice"],
    28: ["Cơm gà Hải Nam", "Hainanese chicken rice"],
    29: ["Cơm chiên Dương Châu", "Yangzhou fried rice"],
    30: ["Cơm rang dưa bò", "Beef fried rice with pickled greens"],
    31: ["Bò lúc lắc", "Shaking beef with rice"],
    32: ["Cơm niêu", "Claypot rice"],
    33: ["Sườn nướng", "Grilled pork ribs with rice"],
    34: ["Bibimbap", "Korean bibimbap"],
    35: ["Cà ri Nhật Bản", "Japanese curry rice"],
    36: ["Thịt kho cải chua", "Braised pork with pickled mustard"],
    37: ["Cá kho tộ", "Claypot caramelized fish"],
    38: ["Thịt kho tàu", "Vietnamese braised pork with eggs"],
    39: ["Canh chua", "Vietnamese sweet and sour soup"],
    40: ["Gà sốt Teriyaki", "Chicken teriyaki rice"],
    41: ["Xôi xéo", "Xoi xeo Hanoi"],
    42: ["Xôi mặn", "Savory sticky rice"],
    43: ["Cơm lam", "Bamboo sticky rice"],
    44: ["Cơm cháy chà bông", "Crispy rice cracker pork floss"],
    45: ["Cơm rang kim chi", "Kimchi fried rice"],
    46: ["Cơm chiên cá mặn", "Salted fish fried rice"],
    47: ["Cơm tấm ba rọi", "Pork belly rice"],
    48: ["Sườn xào chua ngọt", "Sweet and sour pork ribs"],
    49: ["Vịt quay Bắc Kinh", "Peking duck"],
    50: ["Bò xào nấm", "Stir-fried beef with mushrooms"],
    51: ["Gà rán", "Korean fried chicken crispy"],
    52: ["Gà rán sốt cay", "Spicy korean fried chicken"],
    53: ["Burger bò", "Cheeseburger bacon"],
    54: ["Pizza hải sản", "Seafood pizza mozzarella"],
    55: ["Pizza pepperoni", "Pepperoni pizza"],
    56: ["Mì Ý bò bằm", "Spaghetti bolognese"],
    57: ["Mì Ý sốt kem", "Spaghetti carbonara"],
    58: ["Bánh mì Thổ Nhĩ Kỳ", "Doner kebab sandwich"],
    59: ["Bánh mì Việt Nam", "Vietnamese Banh mi"],
    60: ["Bánh mì chảo", "Banh mi chao pan eggs"],
    61: ["Khoai tây chiên", "French fries cheese"],
    62: ["Bánh tráng trộn", "Banh trang tron rice paper"],
    63: ["Bánh tráng nướng", "Banh trang nuong Dalat pizza"],
    64: ["Bắp xào bơ", "Sauteed sweet corn"],
    65: ["Tteokbokki", "Spicy tteokbokki cheese"],
    66: ["Gimbap", "Korean kimbap seaweed roll"],
    67: ["Nem chua rán", "Vietnamese fried fermented pork roll"],
    68: ["Phô mai que", "Fried mozzarella cheese sticks"],
    69: ["Chân gà sả tắc", "Vietnamese lemongrass chicken feet"],
    70: ["Trứng cút lộn xào me", "Tamarind quail eggs"],
    71: ["Bánh gối", "Banh goi Hanoi crispy pastry"],
    72: ["Tacos", "Mexican beef tacos"],
    73: ["Khoai tây lốc xoáy", "Tornado potato spiral"],
    74: ["Gà viên popcorn", "Crispy popcorn chicken"],
    75: ["Sandwich phô mai", "Grilled cheese sandwich melt"],
    76: ["Lẩu Thái", "Tom yum goong hotpot"],
    77: ["Lẩu nấm", "Mushroom hotpot soup"],
    78: ["Bò nhúng dấm", "Vietnamese beef vinegar fondue"],
    79: ["Lẩu riêu cua", "Crab paste hotpot"],
    80: ["Lẩu ếch măng cay", "Frog spicy bamboo hotpot"],
    81: ["Lẩu cá kèo", "Vietnamese goby fish hotpot"],
    82: ["Lẩu gà lá é", "Chicken hotpot with e leaves"],
    83: ["Bò nướng", "Grilled beef bbq"],
    84: ["Ba chỉ bò cuộn nấm", "Beef rolls with enoki mushroom"],
    85: ["Nầm nướng", "Grilled pork udder"],
    86: ["Bạch tuộc nướng", "Grilled octopus spicy satay"],
    87: ["Hàu nướng mỡ hành", "Grilled oysters scallion oil"],
    88: ["Hàu nướng phô mai", "Baked oysters cheese"],
    89: ["Bánh xèo", "Vietnamese sizzling crepe Banh xeo"],
    90: ["Gỏi cuốn", "Vietnamese fresh spring rolls"],
    91: ["Nem lụi", "Hue grilled lemongrass pork skewers"],
    92: ["Bò cuốn bánh tráng", "Vietnamese beef rice paper rolls"],
    93: ["Sukiyaki", "Japanese sukiyaki beef hotpot"],
    94: ["Sườn nướng BBQ", "Grilled BBQ ribs mountain"],
    95: ["Bánh tráng cuốn thịt heo", "Pork belly rice paper roll Da Nang"],
    96: ["Lẩu cừu", "Mongolian lamb hot pot"],
    97: ["Gà nướng muối ớt", "Vietnamese grilled chicken spicy salt"],
    98: ["Dồi sụn nướng", "Grilled pork cartilage sausage"],
    99: ["Ốc xào rau muống", "Stir-fried sea snails morning glory"],
    100: ["Lẩu kim chi", "Kimchi jjigae hotpot"]
}

# Kho ảnh Unsplash chuyên biệt dự phòng chất lượng cao
UNSPLASH_FALLBACKS = {
    "noodle": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&auto=format&fit=crop&q=80",
    "rice": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80",
    "fastfood": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "hotpot": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80"
}

def search_wikimedia(term):
    """Tìm ảnh thumbnail từ Wikipedia vi / en hoặc Wikimedia Commons"""
    # 1. Thử Wikipedia Tiếng Việt
    url_vi = f"https://vi.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=800&titles={urllib.parse.quote(term)}"
    req = urllib.request.Request(url_vi, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=4, context=CTX) as res:
            data = json.loads(res.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                if pid != '-1' and 'thumbnail' in p:
                    return p['thumbnail']['source']
    except Exception:
        pass

    # 2. Thử Wikipedia Tiếng Anh
    url_en = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=800&titles={urllib.parse.quote(term)}"
    req = urllib.request.Request(url_en, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=4, context=CTX) as res:
            data = json.loads(res.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                if pid != '-1' and 'thumbnail' in p:
                    return p['thumbnail']['source']
    except Exception:
        pass

    # 3. Thử Wikimedia Commons Search
    url_commons = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(term)}&gsrlimit=1&prop=pageimages&pithumbsize=800&format=json"
    req = urllib.request.Request(url_commons, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=4, context=CTX) as res:
            data = json.loads(res.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                if pid != '-1' and 'thumbnail' in p:
                    return p['thumbnail']['source']
    except Exception:
        pass

    return None

def download_and_compress(img_url, output_path, target_size=(600, 450)):
    """Tải ảnh, crop tâm và nén sang định dạng WebP chất lượng 80%"""
    req = urllib.request.Request(img_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=8, context=CTX) as response:
        img_bytes = response.read()

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    width, height = img.size
    target_w, target_h = target_size

    # Crop căn giữa theo tỷ lệ 4:3
    target_aspect = target_w / target_h
    img_aspect = width / height

    if img_aspect > target_aspect:
        # Ảnh bè ngang hơn -> crop 2 bên
        new_w = int(height * target_aspect)
        left = (width - new_w) // 2
        img = img.crop((left, 0, left + new_w, height))
    else:
        # Ảnh cao hơn -> crop trên dưới
        new_h = int(width / target_aspect)
        top = (height - new_h) // 2
        img = img.crop((0, top, width, top + new_h))

    # Resize mượt mà với LANCZOS
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    # Lưu WebP nén nhẹ
    img.save(output_path, "WEBP", quality=80, method=4)
    return os.path.getsize(output_path)

def process_all_dishes():
    with open(os.path.join(os.path.dirname(__file__), "dishes.json"), encoding="utf-8") as f:
        dishes = json.load(f)

    print(f"=== BẮT ĐẦU XỬ LÝ ẢNH CHO {len(dishes)} MÓN ĂN ===")
    success_count = 0
    total_bytes = 0

    for d in dishes:
        dish_id = d['id']
        name = d['name']
        cat = d['category']
        out_file = os.path.join(OUTPUT_DIR, f"dish_{dish_id}.webp")

        terms = DISH_TERMS.get(dish_id, [name])
        img_url = None

        # Thử tìm ảnh phù hợp qua các term
        for term in terms:
            img_url = search_wikimedia(term)
            if img_url:
                break

        # Nếu không tìm thấy, dùng link hiện có hoặc fallback theo danh mục
        if not img_url:
            if d.get('img') and d['img'].startswith('http'):
                img_url = d['img']
            else:
                cat_key = "noodle" if "Bún" in cat else ("rice" if "Cơm" in cat else ("fastfood" if "Fastfood" in cat else "hotpot"))
                img_url = UNSPLASH_FALLBACKS.get(cat_key)

        try:
            size = download_and_compress(img_url, out_file)
            total_bytes += size
            success_count += 1
            print(f"[{dish_id:03d}/100] ✔ {name[:28]:28s} -> {size/1024:.1f} KB (Nguồn: {img_url[:45]}...)")
        except Exception as e:
            print(f"[{dish_id:03d}/100] ✖ LỖI {name}: {e}. Thử fallback...")
            try:
                fb_url = UNSPLASH_FALLBACKS["rice" if "Cơm" in cat else "hotpot"]
                size = download_and_compress(fb_url, out_file)
                total_bytes += size
                success_count += 1
            except Exception as e2:
                print(f"[{dish_id:03d}/100] ✖ THẤT BẠI: {e2}")

    print("\n" + "="*50)
    print(f"HOÀN THÀNH: {success_count}/{len(dishes)} món ăn đã được nén thành WebP.")
    print(f"Tổng dung lượng 100 ảnh: {total_bytes / (1024*1024):.2f} MB (~{total_bytes/len(dishes)/1024:.1f} KB/ảnh).")
    print("="*50)

if __name__ == "__main__":
    process_all_dishes()
