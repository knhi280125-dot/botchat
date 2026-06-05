import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# =====================================================================
# 🚨 EM DÁN MÃ TOKEN SIÊU DÀI THẬT CỦA EM VÀO GIỮA HAI DẤU NHÁY ĐƠN Ở DÒNG DƯỚI:
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'BeaPywxIo94ZyuzaqqeoK0AhzWXL6AlickU2iJIuCqIQKb7zbGCu3RvwacAIOQbQtBrgzhBnP9ouY77TdhaZAZ95N7PHrHGIIBZGtrIJRfoSaKjU21/dHRNY2yZCmkjRPTx6dkxofgG5Mc3jCbBypAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '5cf621e2ac85e6049ed1ea8b66d6a806')
# =====================================================================

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot Weather & AQI Master Pro is Running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# --- HÀM GỌI API AQI ĐÀI LOAN ---
def get_taiwan_aqi(location_name):
    try:
        url = "https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3de7ef334c1&limit=1000&format=JSON"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code != 200:
            return "⚠️ 系統連線異常，請稍後再試！"
            
        data = response.json()
        records = data.get('records', [])
        
        for record in records:
            site = record.get('sitename', '')
            county = record.get('county', '')
            
            if location_name in site or location_name in county:
                aqi_val = record.get('aqi')
                if not aqi_val or aqi_val == '無資料':
                    continue
                    
                aqi = int(aqi_val)
                status = record.get('status', '未知')
                pm25 = record.get('pm2.5', '無資料')
                
                if aqi <= 50:
                    advice = "🟢 空氣良好，免戴口罩 (Không khí tốt, miễn đeo khẩu trang)."
                elif aqi <= 100:
                    advice = "🟡 空氣普通，敏感族群出門建議配戴口罩 (Không khí bình thường, nhóm nhạy cảm nên đeo)."
                else:
                    advice = "🔴 空氣不良，出門請務必配戴口罩！(Không khí ô nhiễm, bắt buộc đeo khẩu trang!)"
                
                return f"📍 觀測站: {county} - {site}\n😷 AQI 指數: {aqi} ({status})\n🔹 PM2.5: {pm25} μg/m³\n💡 健康建議: {advice}"
                
        return f"找不到「{location_name}」的觀測資料，請輸入台灣縣市名稱（如：台北、台中）。"
    except Exception:
        return "⚠️ 系統 busy，請稍後再試！"

# --- 🧠 BỘ NÃO AI PHÂN TÍCH 15 KỊCH BẢN CHUYÊN NGHIỆP ---
def call_ai_assistant(user_message):
    msg = user_message.strip().upper()
    
    # --- NHÓM 1: TÍNH NĂNG & TRẢI NGHIỆM ---
    if "功能" in msg or "FEATURES" in msg:
        return "🤖 【系統核心功能】\n1. 即時查詢：動態串接政府 Open Data，秒級回覆台灣各縣市 AQI 與 PM2.5 數據。\n2. 智慧問答：內建 AI 語意識別，能自動解答環境、健康與系統架構等延伸問題。\n3. 直覺介面：整合 LINE 聊天室，免下載應用程式，隨掃隨用。"
        
    elif "使用" in msg or "操作" in msg or "HOW" in msg:
        return "🤖 【系統操作指南】\n1. 輸入台灣縣市或測站名稱（例如：台北、西屯、高雄），系統會自動秒查當地最新 AQI 指數。\n2. 輸入關鍵字如「動機」、「特色」、「架構」、「健康建議」，即可獲得系統的智慧分析喔！"
        
    elif "健康" in msg or "建議" in msg or "ADVICE" in msg:
        return "🤖 【AI 呼吸健康建議】\n當 AQI > 100 (橘色/紅色預警) 時，細懸浮微粒容易引發呼吸道不適。建議年長者、過敏族群與孩童減少戶外劇烈運動，出門請務必配戴高防護口罩，並開啟室內空氣清淨機。"
        
    elif "PM2.5" in msg or "細懸浮微粒" in msg:
        return "🤖 【什麼是 PM2.5？】\nPM2.5 是指粒徑小於或等於 2.5 微米的細懸浮微粒。因為體積微小，它能穿透肺泡直接進入血管循環，對心血管造成慢性危害。是目前台灣大眾最關心的環境健康指標！"
        
    elif "空氣不好" in msg or "空污" in msg:
        return "🤖 【空污防護應變對策】\n1. 減少開窗：避免戶外細懸浮微粒進入室內。\n2. 高效防護：若必須出門，普通布口罩無效，請配戴醫用口罩或 N95 口罩。\n3. 科技輔助：建議室內開啟帶有 HEPA 濾網的空氣清淨機，維持良好生活品質。"

    # --- NHÓM 2: KỸ THUẬT MIS & ẢNH HƯỞNG ---
    elif "動機" in msg or "WHY" in msg:
        return "🤖 【開發動機】\n為了解決大眾日常查詢天氣與空污（AQI）時步驟繁瑣的痛點。本系統利用 LINE 平台免下載、隨掃即用的優勢，結合政府 Open Data 與 AI 技術，提供最直覺、秒級回覆的健康生活助手！"
        
    elif "架構" in msg or "STRUCTURE" in msg:
        return "🤖 【系統架構】\n本專案為標準的 MIS 資訊系統應用：\n1. 前端 UI：LINE Webhook 接收端與 Rich Menu 圖文選單。\n2. 後端 Web Server：Python Flask 輕量級網頁框架。\n3. 雲端部署：Render Deployment Cloud。\n4. 資料層：串接台灣環境部 開放資料 API (Open Data API)。"
        
    elif "特色" in msg or "BENEFIT" in msg:
        return "🤖 【系統三大特色】\n1. 【即時同步】：動態串接政府最新觀測站數據。\n2. 【智慧互動】：內建 AI 語意判斷，自動識別用戶核心需求。\n3. 【免下載跨平台】：直接嵌入 LINE 聊天室，用戶體驗極佳。"
        
    elif "FLASK" in msg or "選擇" in msg:
        return "🤖 【技術選型：Python Flask】\n選擇 Flask 框架是因為它具有輕量級、高擴充性與微服務（Microservices）架構的特性。能完美契合 LINE Webhook 的監聽與響應需求，大幅降低系統延遲，提升 MIS 專案的開發效率。"
        
    elif "WEBHOOK" in msg or "觸發" in msg:
        return "🤖 【技術科普：什麼是 Webhook？】\nWebhook 是一種「事件驅動」的資料傳輸機制。當用戶在 LINE 發送訊息時，LINE 伺服器會立即觸發事件，並將 JSON 資料推送到我們部署在 Render 的 Flask 接收端。這比傳統的輪詢（Polling）更省資源、更具即時性。"

    # --- NHÓM 3: GIÁ TRỊ HỌC THUẬT & QUẢN LÝ ---
    elif "開放資料" in msg or "OPEN DATA" in msg:
        return "🤖 【MIS 核心：開放資料 (Open Data) 應用】\n本專案透過環境部 API 實踐了「政府資料開放」的商業應用價值。將原本雜亂的原始 JSON 數據，透過後端邏輯清洗與結構化，轉化為對用戶有價值的「決策資訊」，展現了資訊管理（Information Management）的核心精神。"
        
    elif "來源" in msg or "DATA SOURCE" in msg:
        return "🤖 【資料來源與真實性】\n本系統之環境觀測數據，100% 串接自台灣政府「環境部環境資料開放平台」（MOENV Open Data）。數據每小時動態更新，確保空氣品質指數（AQI）與 PM2.5 觀測值的權威性與即時性。"
        
    elif "未來" in msg or "展望" in msg:
        return "🤖 【系統未來優化展望】\n1. 實時推播：未來計畫導入定時主動推播功能，當用戶所在地空污超標時自動示警。\n2. LBS 定位：結合 LINE 位置訊息功能（Location-Based Service），讓用戶一鍵傳送定位即可查詢最近的觀測站。\n3. 大數據預測：結合機器學習，預測未來 24 小時의 空氣品質趨勢。"
        
    elif "商業" in msg or "價值" in msg:
        return "🤖 【專案的社會與商業價值】\n本系統具備極高的 ESG（環境、社會、公司治理）應用潛力。能作為企業內部員工健康福利小幫手，亦能推廣為社區公共衛生的數位微服務，用資訊科技（IT）切實提升大眾對環境保護的自覺與健康防護。"
        
    elif "結論" in msg or "成果" in msg:
        return "🤖 【專案成果總結】\n本專案成功結合理論與實務，將 Python 後端開發、雲端部署與行動社群平台（LINE）進行深度整合。證明了利用輕量級架構，資訊管理系統（MIS）能在極短時間內開發出敏捷、實用且兼具社會價值的數位創新服務。"
        
    else:
        return f"🤖 【AI 智慧助手】\n我已收到您的訊息：「{user_message}」\n這是一個結合 LINE Bot 與 Python 後端的智慧 Demo。您可以試著輸入「動機」、「特色」、「系統功能」、「系統架構」或「PM2.5」來測試我的學術報告專用功能喔！"

# --- XỬ LÝ TIN NHẮN TỪ USER ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    
    # Nhận diện nếu tra cứu theo vùng miền
    if any(keyword in user_msg for keyword in ["空氣", "天氣", "AQI", "台北", "台中", "高雄", "台南", "新竹", "西屯"]):
        clean_msg = user_msg.replace("空氣", "").replace("天氣", "").replace("品質", "").strip()
        if not clean_msg:
            clean_msg = "台北"
        reply_text = get_taiwan_aqi(clean_msg)
    else:
        # Tự động đẩy qua kịch bản AI phản hồi chuyên nghiệp
        reply_text = call_ai_assistant(user_msg)
        
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
