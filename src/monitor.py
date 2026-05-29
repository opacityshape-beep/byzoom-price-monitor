#!/usr/bin/env python3
"""
BYZOOM FITNESS 每日巡價監控工具
每天自動比對各電商平台價格，發現破價立即通知
"""

import requests
import smtplib
import json
import time
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup
import os

# ============================================================
# 設定區（GitHub Actions Secrets 帶入）
# ============================================================
GMAIL_USER        = os.environ.get("GMAIL_USER", "")
GMAIL_PASSWORD    = os.environ.get("GMAIL_PASSWORD", "")
NOTIFY_EMAIL      = os.environ.get("NOTIFY_EMAIL", "")
TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "8839726246")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# ============================================================
# 官網商品清單與售價（排除七龍珠）
# ============================================================
OFFICIAL_PRODUCTS = [
    # === 可調式啞鈴 Pure Series ===
    {"title": "Pure Series 5.6kg(12.5LB) 5段重量 可調式啞鈴(白)", "price": 1980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-12-5lb-white"},
    {"title": "Pure Series 5.6kg(12.5LB) 5段重量 可調式啞鈴(黑)", "price": 1980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-12-5lb-black"},
    {"title": "Pure Series 11.3kg(25LB) 5段重量 可調式啞鈴(白)", "price": 3280, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-25lb-white"},
    {"title": "Pure Series 11.3kg(25LB) 5段重量 可調式啞鈴(黑)", "price": 3280, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-25lb-black"},
    {"title": "Pure Series 12.5kg(27.5LB) 10段重量 可調式啞鈴(白)", "price": 3980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-27-5lb-white"},
    {"title": "Pure Series 12.5kg(27.5LB) 10段重量 可調式啞鈴(黑)", "price": 3980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-27-5lb-black"},
    {"title": "Pure Series 22.6kg(50LB) 5段重量 可調式啞鈴(白)", "price": 4980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-50lb-white"},
    {"title": "Pure Series 22.6kg(50LB) 5段重量 可調式啞鈴(黑)", "price": 4980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-50lb-black"},
    {"title": "Pure Series 25kg(55LB) 15段重量 可調式啞鈴(白)", "price": 5980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-55lb-white"},
    {"title": "Pure Series 25kg(55LB) 15段重量 可調式啞鈴(黑)", "price": 5980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-55lb-black"},
    {"title": "Pure Series 34kg(75LB) 21段重量 可調式啞鈴(黑)", "price": 7980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-75lb-black"},
    # === 可調式啞鈴 Classic Series ===
    {"title": "Classic Series 22.6kg(50LB) 5段重量 可調式啞鈴(黑)", "price": 4000, "url": "https://byzoomfitness.com/products/classic-series-adjustable-dumbbell-50lb-black"},
    {"title": "Classic Series 25kg(55LB) 15段重量 可調式啞鈴(黑)", "price": 4800, "url": "https://byzoomfitness.com/products/classic-series-adjustable-dumbbell-55lb-black"},
    # === 可調式壺鈴 Pure Series ===
    {"title": "Pure Series 13.6kg(30LB) 5段重量 可調式壺鈴(白)", "price": 2980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-30lb-white"},
    {"title": "Pure Series 13.6kg(30LB) 5段重量 可調式壺鈴(黑)", "price": 2980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-30lb-black"},
    {"title": "Pure Series 18.1kg(40LB) 5段重量 可調式壺鈴(白)", "price": 3980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-40lb-white"},
    {"title": "Pure Series 18.1kg(40LB) 5段重量 可調式壺鈴(黑)", "price": 3980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-40lb-black"},
    {"title": "Pure Series 22.6kg(50LB) 5段重量 可調式壺鈴(白)", "price": 4980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-50lb-white"},
    {"title": "Pure Series 22.6kg(50LB) 5段重量 可調式壺鈴(黑)", "price": 4980, "url": "https://byzoomfitness.com/products/pure-series-adjustable-kettlebell-50lb-black"},
    # === 可調式槓鈴 ===
    {"title": "Pure Series 36.2kg(80LB) 14段重量 可調式槓鈴(黑)", "price": 8800, "url": "https://byzoomfitness.com/products/pure-series-adjustable-barbell-80lb-black"},
    {"title": "Pure Series Max 45.3kg(100LB) 可調式槓鈴轉換架(黑)", "price": 11800, "url": "https://byzoomfitness.com/products/pure-series-barbell-converter-55lb-black"},
    {"title": "Pure Series Max 45.3kg(100LB) 可調式槓鈴轉換架(白)", "price": 11800, "url": "https://byzoomfitness.com/products/pure-series-barbell-converter-55lb-white"},
    {"title": "Pure Series Max 63.5kg(140LB) 可調式槓鈴轉換架(黑)", "price": 13800, "url": "https://byzoomfitness.com/products/pure-series-barbell-converter-75lb-black"},
    {"title": "Pure Series Easy Bar 4.5KG(10LB) 專用槓鈴桿(白)", "price": 1680, "url": "https://byzoomfitness.com/products/pure-series-easy-bar-10lb-white"},
    {"title": "Pure Series Easy Bar 4.5KG(10LB) 專用槓鈴桿(黑)", "price": 1680, "url": "https://byzoomfitness.com/products/pure-series-easy-bar-10lb-black"},
    # === 健身椅 ===
    {"title": "Pure Series 站立式收納5段調整健身椅(白)", "price": 5980, "url": "https://byzoomfitness.com/products/pure-series-foldable-bench-white"},
    {"title": "Pure Series 站立式收納5段調整健身椅(黑)", "price": 5980, "url": "https://byzoomfitness.com/products/pure-series-foldable-bench-black"},
    # === 啞鈴專用架 ===
    {"title": "Pure Series 5.6/11.3/12.5kg 可調式啞鈴專用架(白)", "price": 2480, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-stand-12-5lb-25lb-white"},
    {"title": "Pure Series 5.6/11.3/12.5kg 可調式啞鈴專用架(黑)", "price": 2480, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-stand-12-5lb-25lb-black"},
    {"title": "Pure Series 22.6kg/25kg 可調式啞鈴專用架(白)", "price": 2380, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-stand-50lb-55lb-white"},
    {"title": "Pure Series 22.6kg/25kg 可調式啞鈴專用架(黑)", "price": 2380, "url": "https://byzoomfitness.com/products/pure-series-adjustable-dumbbell-stand-50lb-55lb-black"},
    {"title": "Classic Series 可調式啞鈴專用架(黑)", "price": 1980, "url": "https://byzoomfitness.com/products/classic-series-adjustable-dumbbell-stand-50lb-55lb-black"},
    # === 瑜珈配件 ===
    {"title": "TPE 止滑輕巧瑜珈墊 4mm (淺粉)", "price": 980, "url": "https://byzoomfitness.com/products/tpe-yogamat-4mm-light-pink"},
    {"title": "TPE 止滑輕巧瑜珈墊 4mm (紫)", "price": 980, "url": "https://byzoomfitness.com/products/tpe-yogamat-4mm-purple"},
    {"title": "TPE 止滑輕巧瑜珈墊 4mm (灰)", "price": 980, "url": "https://byzoomfitness.com/products/tpe-yogamat-4mm-gray"},
    {"title": "PU天然橡膠瑜珈墊5mm (黑)", "price": 1480, "url": "https://byzoomfitness.com/products/pu-natural-rubber-yogamat-5mm-black"},
    {"title": "TPE 健身墊 8mm (白)", "price": 680, "url": "https://byzoomfitness.com/products/tpe-exercise-8mm-white"},
    {"title": "PVC 瑜珈墊 5MM (松金)", "price": 490, "url": "https://byzoomfitness.com/products/pvc-yoga-mat-5mm-green"},
    {"title": "PVC 瑜珈墊 5MM (馬卡龍)", "price": 490, "url": "https://byzoomfitness.com/products/pvc-yoga-mat-5mm-blue"},
    {"title": "瑜珈繩(粉紫)", "price": 290, "url": "https://byzoomfitness.com/products/yoga-strap-purple"},
    {"title": "瑜珈墊背帶(粉紫)", "price": 350, "url": "https://byzoomfitness.com/products/yoga-mat-carrier-purple"},
    # === 按摩舒緩系列 ===
    {"title": "大理石紋 強化版按摩滾筒", "price": 990, "url": "https://byzoomfitness.com/products/marble-pattern-series-intense-foam-roller"},
    {"title": "大理石紋 舒緩版按摩滾筒", "price": 650, "url": "https://byzoomfitness.com/products/marble-pattern-series-foam-roller"},
    {"title": "大理石紋 按摩球", "price": 290, "url": "https://byzoomfitness.com/products/marble-pattern-series-massage-ball"},
    {"title": "大理石紋 瑜珈磚", "price": 390, "url": "https://byzoomfitness.com/products/marble-pattern-series-yogablock"},
    {"title": "淺羊絨色強化按摩滾筒", "price": 990, "url": "https://byzoomfitness.com/products/foam-roller-cashmere-colored"},
    {"title": "淺羊絨色按摩球", "price": 290, "url": "https://byzoomfitness.com/products/massage-ball-cashmere-colored"},
    {"title": "天然軟木按摩球", "price": 290, "url": "https://byzoomfitness.com/products/massage-ball-cork"},
    {"title": "天然橡膠按摩花生球", "price": 290, "url": "https://byzoomfitness.com/products/natural-rubber-double-massage-ball"},
    # === 訓練配件 ===
    {"title": "健腹滾輪+(白)", "price": 890, "url": "https://byzoomfitness.com/products/ab-roller-plus-white"},
    {"title": "健腹滾輪+(黑)", "price": 890, "url": "https://byzoomfitness.com/products/ab-roller-plus-black"},
    {"title": "健腹滾輪", "price": 490, "url": "https://byzoomfitness.com/products/ab-roller-black"},
    {"title": "俯臥撐支架+(白)", "price": 790, "url": "https://byzoomfitness.com/products/push-up-handle-plus-white"},
    {"title": "俯臥撐支架+(黑)", "price": 790, "url": "https://byzoomfitness.com/products/push-up-handle-plus-black"},
    {"title": "1KG 皮拉提斯球(黑)", "price": 450, "url": "https://byzoomfitness.com/products/mini-pilates-ball-black"},
    # === 凱蒂瑜珈系列 ===
    {"title": "凱蒂瑜珈 Flow With Katie 天然橡膠瑜珈墊5mm", "price": 1680, "url": "https://byzoomfitness.com/products/katie-nbmat"},
    {"title": "凱蒂瑜珈 Flow With Katie TPE 止滑輕巧瑜珈墊 6mm", "price": 1280, "url": "https://byzoomfitness.com/products/katie-tpemat"},
    {"title": "凱蒂瑜珈 Flow With Katie 瑜珈磚", "price": 390, "url": "https://byzoomfitness.com/products/katie-yogablock"},
    {"title": "凱蒂瑜珈 Flow With Katie 霧面止滑防爆健身球", "price": 600, "url": "https://byzoomfitness.com/products/katie-gymball"},
    {"title": "凱蒂瑜珈 Flow With Katie 天然橡膠按摩球", "price": 290, "url": "https://byzoomfitness.com/products/katie-massageball"},
]


# ============================================================
# 搜尋各平台
# ============================================================

def search_momo(keyword):
    results = []
    url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={requests.utils.quote(keyword)}&searchType=1&curPage=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.goodsItemLi")[:5]:
            name_el = item.select_one(".prdName")
            price_el = item.select_one(".price b")
            link_el = item.select_one("a[href]")
            if not (name_el and price_el): continue
            name = name_el.get_text(strip=True)
            if "byzoom" not in name.lower(): continue
            try:
                price = float(re.sub(r"[^\d.]", "", price_el.get_text(strip=True).replace(",", "")))
            except: continue
            if price < 100: continue
            link = link_el["href"] if link_el else url
            if not link.startswith("http"): link = "https://www.momoshop.com.tw" + link
            results.append({"platform": "momo購物", "name": name, "price": price, "url": link})
    except Exception as e:
        print(f"    ⚠️ momo: {e}")
    return results


def search_pchome(keyword):
    results = []
    url = f"https://24h.pchome.com.tw/search/?q={requests.utils.quote(keyword)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.prod-item, div.prod-item")[:5]:
            name_el = item.select_one(".prod-name, .title")
            price_el = item.select_one(".price, .prod-price")
            link_el = item.select_one("a[href]")
            if not (name_el and price_el): continue
            name = name_el.get_text(strip=True)
            try:
                price = float(re.sub(r"[^\d.]", "", price_el.get_text(strip=True).replace(",", "")))
            except: continue
            if price < 100: continue
            link = link_el["href"] if link_el else url
            if not link.startswith("http"): link = "https://24h.pchome.com.tw" + link
            results.append({"platform": "PChome", "name": name, "price": price, "url": link})
    except Exception as e:
        print(f"    ⚠️ PChome: {e}")
    return results


def search_yahoo(keyword):
    results = []
    url = f"https://tw.buy.yahoo.com/search/product?p={requests.utils.quote(keyword)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.LoopProduct, div[data-product-id]")[:5]:
            name_el = item.select_one(".Productname, .title, h3")
            price_el = item.select_one(".Price, [class*='price']")
            link_el = item.select_one("a[href]")
            if not (name_el and price_el): continue
            name = name_el.get_text(strip=True)
            try:
                price = float(re.sub(r"[^\d.]", "", price_el.get_text(strip=True).replace(",", "")))
            except: continue
            if price < 100: continue
            link = link_el["href"] if link_el else url
            if not link.startswith("http"): link = "https://tw.buy.yahoo.com" + link
            results.append({"platform": "Yahoo購物", "name": name, "price": price, "url": link})
    except Exception as e:
        print(f"    ⚠️ Yahoo: {e}")
    return results


def search_shopee(keyword):
    results = []
    api_url = (
        f"https://shopee.tw/api/v4/search/search_items"
        f"?by=relevancy&keyword={requests.utils.quote(keyword)}"
        f"&limit=10&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2"
    )
    try:
        resp = requests.get(api_url, headers={**HEADERS, "Referer": "https://shopee.tw/"}, timeout=15)
        data = resp.json()
        for item in (data.get("items") or [])[:5]:
            info = item.get("item_basic", item)
            name = info.get("name", "")
            if "byzoom" not in name.lower(): continue
            price_raw = info.get("price") or info.get("price_min") or 0
            price = price_raw / 100000
            if price < 100: continue
            shop_id = info.get("shopid", "")
            item_id = info.get("itemid", "")
            link = f"https://shopee.tw/product/{shop_id}/{item_id}" if shop_id else "https://shopee.tw"
            results.append({"platform": "蝦皮購物", "name": name, "price": price, "url": link})
    except Exception as e:
        print(f"    ⚠️ 蝦皮: {e}")
    return results


def search_coupang(keyword):
    results = []
    url = f"https://www.coupang.com/np/search?component=&q={requests.utils.quote(keyword)}&channel=user"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.search-product")[:5]:
            name_el = item.select_one(".name")
            price_el = item.select_one(".price-value")
            link_el = item.select_one("a[href]")
            if not (name_el and price_el): continue
            name = name_el.get_text(strip=True)
            try:
                price = float(re.sub(r"[^\d.]", "", price_el.get_text(strip=True).replace(",", "")))
            except: continue
            if price < 100: continue
            link = link_el["href"] if link_el else url
            if not link.startswith("http"): link = "https://www.coupang.com" + link
            results.append({"platform": "酷澎Coupang", "name": name, "price": price, "url": link})
    except Exception as e:
        print(f"    ⚠️ 酷澎: {e}")
    return results


# ============================================================
# 比對價格
# ============================================================

def find_violations():
    violations = []
    scanned = 0
    total = len(OFFICIAL_PRODUCTS)

    for i, product in enumerate(OFFICIAL_PRODUCTS):
        title = product["title"]
        official_price = product["price"]
        official_url = product["url"]

        keyword = re.sub(r"[（(][白黑][)）]", "", title).strip()
        keyword = f"BYZOOM {keyword[:25]}"

        print(f"  [{i+1}/{total}] {title[:35]}  官網 TWD${official_price:,}")

        all_results = []
        for searcher in [search_momo, search_pchome, search_yahoo, search_shopee, search_coupang]:
            all_results.extend(searcher(keyword))
            time.sleep(0.3)

        for r in all_results:
            if 100 < r["price"] < official_price:
                diff = official_price - r["price"]
                violations.append({
                    "product": title,
                    "official_price": official_price,
                    "official_url": official_url,
                    "platform": r["platform"],
                    "platform_price": r["price"],
                    "platform_name": r["name"],
                    "platform_url": r["url"],
                    "diff": diff,
                    "diff_pct": (diff / official_price) * 100,
                })
        scanned += len(all_results)
        time.sleep(0.5)

    return violations, scanned


# ============================================================
# Telegram 通知
# ============================================================

def send_telegram(violations):
    if not TELEGRAM_TOKEN:
        print("⚠️  TELEGRAM_TOKEN 未設定，跳過")
        return

    if violations:
        lines = ["🚨 *BYZOOM 破價警報！*\n"]
        for v in violations:
            lines.append(
                f"📦 *{v['product'][:35]}*\n"
                f"🏪 平台：{v['platform']}\n"
                f"💰 官網：TWD${v['official_price']:,}　→　平台：TWD${v['platform_price']:,}\n"
                f"📉 便宜了 TWD${v['diff']:,}（{v['diff_pct']:.1f}%）\n"
                f"🔗 [查看商品]({v['platform_url']})\n"
            )
        msg = "\n".join(lines)
    else:
        msg = "✅ *BYZOOM 今日巡價正常*\n\n所有平台價格均未低於官網，一切 OK 👍"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }, timeout=15)
        if resp.status_code == 200:
            print("✅ Telegram 通知發送成功")
        else:
            print(f"⚠️  Telegram 回應：{resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Telegram 發送失敗：{e}")


# ============================================================
# Email 報告
# ============================================================

def build_html(violations, scanned, scan_time):
    has_v = len(violations) > 0

    rows = ""
    for v in violations:
        rows += f"""<tr style="background:#fff3f3">
          <td style="padding:8px;border:1px solid #ddd">{v['product'][:45]}</td>
          <td style="padding:8px;border:1px solid #ddd;text-align:center">{v['platform']}</td>
          <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#999">TWD${v['official_price']:,}</td>
          <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#c00;font-weight:bold">
            <a href="{v['platform_url']}" style="color:#c00">TWD${v['platform_price']:,}</a>
          </td>
          <td style="padding:8px;border:1px solid #ddd;text-align:center;color:#c00">▼ ${v['diff']:,} ({v['diff_pct']:.1f}%)</td>
        </tr>"""

    banner = (
        f'<div style="background:#c00;color:#fff;padding:15px;border-radius:6px;margin-bottom:20px;font-size:18px;font-weight:bold">🚨 發現 {len(violations)} 筆破價！請立即確認</div>'
        if has_v else
        '<div style="background:#2e7d32;color:#fff;padding:15px;border-radius:6px;margin-bottom:20px;font-size:18px;font-weight:bold">✅ 今日巡價正常，未發現破價</div>'
    )

    table = f"""<h2 style="color:#c00">⚠️ 破價商品清單</h2>
      <table style="width:100%;border-collapse:collapse;margin-bottom:30px">
        <thead><tr style="background:#c00;color:#fff">
          <th style="padding:10px;border:1px solid #ddd">商品名稱</th>
          <th style="padding:10px;border:1px solid #ddd">平台</th>
          <th style="padding:10px;border:1px solid #ddd">官網售價</th>
          <th style="padding:10px;border:1px solid #ddd">平台售價</th>
          <th style="padding:10px;border:1px solid #ddd">差異</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>""" if has_v else ""

    return f"""<html><body style="font-family:Arial,sans-serif;max-width:900px;margin:0 auto;padding:20px;color:#333">
      <div style="background:#1d1d1e;color:#fff;padding:20px;border-radius:8px 8px 0 0">
        <h1 style="margin:0;font-size:22px">💪 BYZOOM FITNESS 每日巡價報告</h1>
        <p style="margin:5px 0 0;opacity:.7">掃描時間：{scan_time}</p>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:20px;border-radius:0 0 8px 8px">
        {banner}{table}
        <h2>📊 掃描摘要</h2>
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#f5f5f5"><td style="padding:10px;border:1px solid #ddd">🔍 監控平台</td><td style="padding:10px;border:1px solid #ddd">momo、PChome、Yahoo購物、蝦皮、酷澎</td></tr>
          <tr><td style="padding:10px;border:1px solid #ddd">📦 監控商品數</td><td style="padding:10px;border:1px solid #ddd">{len(OFFICIAL_PRODUCTS)} 款</td></tr>
          <tr style="background:#f5f5f5"><td style="padding:10px;border:1px solid #ddd">📝 比對紀錄數</td><td style="padding:10px;border:1px solid #ddd">{scanned} 筆</td></tr>
          <tr><td style="padding:10px;border:1px solid #ddd">🚨 破價筆數</td>
            <td style="padding:10px;border:1px solid #ddd;color:{'#c00' if has_v else '#2e7d32'};font-weight:bold">{len(violations)} 筆</td></tr>
        </table>
        <p style="margin-top:30px;font-size:12px;color:#999">此為自動巡價系統產生之報告｜BYZOOM FITNESS 巡價監控工具</p>
      </div>
    </body></html>"""


def send_email(subject, html):
    if not all([GMAIL_USER, GMAIL_PASSWORD, NOTIFY_EMAIL]):
        print("⚠️  Email 設定不完整，跳過")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        print(f"✅ Email 寄送成功 → {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"❌ 寄信失敗：{e}")


# ============================================================
# 主程式
# ============================================================

def main():
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}\n🚀 BYZOOM 巡價開始｜{scan_time}\n{'='*60}\n")
    print(f"📦 監控商品數：{len(OFFICIAL_PRODUCTS)} 款（已排除七龍珠）\n")

    violations, scanned = find_violations()

    print(f"\n📊 結果：破價 {len(violations)} 筆 / 比對 {scanned} 筆")
    for v in violations:
        print(f"  🚨 [{v['platform']}] {v['product'][:30]} | 官網${v['official_price']:,} → 平台${v['platform_price']:,} (▼{v['diff_pct']:.1f}%)")

    send_telegram(violations)

    subject = (f"🚨【BYZOOM破價警報】發現{len(violations)}筆破價！{scan_time[:10]}"
               if violations else f"✅【BYZOOM巡價報告】今日正常｜{scan_time[:10]}")
    send_email(subject, build_html(violations, scanned, scan_time))

    with open("price_report.json", "w", encoding="utf-8") as f:
        json.dump({"scan_time": scan_time, "violation_count": len(violations),
                   "violations": violations}, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}\n✅ 巡價完成！\n{'='*60}\n")


if __name__ == "__main__":
    main()
