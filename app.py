import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# =====================================================================
# 🚨 GIỮ NGUYÊN TOKEN CỦA EM Ở ĐÂY (NHỚ THAY MÃ THẬT SIÊU DÀI CỦA EM VÀO NHÉ):
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'BeaPywxIo94ZyuzaqqeoK0AhzWXL6AlickU2iJIuCqIQKb7zbGCu3RvwacAIOQbQtBrgzhBnP9ouY77TdhaZAZ95N7PHrHGIIBZGtrIJRfoSaKjU21/dHRNY2yZCmkjRPTx6dkxofgG5Mc3jCbBypAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '5cf621e2ac85e6049ed1ea8b66d6a806')
# =====================================================================

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=['GET'])
def home():
    return "LINE Bot Weather & AQI is Running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# --- HÀM GỌI API AQI ĐÃ ĐƯỢC TỐI ƯU HÓA ---
def get_taiwan_aqi(location_name):
    try:
        # Sử dụng API mở của Bộ Môi Trường Đài Loan
        url = "https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3de7ef334c1&limit=1000&format=JSON"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code != 200:
            return "⚠️ Không thể kết nối với API dữ liệu chính phủ (Mã lỗi: " + str(response.status_code) + ")."
            
        data = response.json()
        records = data.get('records', [])
        
        # Tìm kiếm thông minh theo từ khóa người dùng nhập
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
                
        return f"找不到「{location_name}」的空氣品質觀測資料，請輸入正確的台灣縣市或測站名稱（例如：台北、西屯）。"
    except Exception as e:
        # Nếu lỗi, in ra một phần thông báo lỗi nhỏ để dễ debug thay vì chỉ báo "busy" chung chung
        return f"❌ 系統連線異常: {str(e)[:50]}... 請稍後再試！"

# --- HÀM GỌI AI ĐỂ TRẢ LỜI CÂU HỎI TỰ DO ---
def call_ai_assistant(user_message):
    if "開發動機" in user_message:
        return "🤖 本系統開發動機：為解決台灣民眾日常查詢空污與天氣的痛點，利用 LINE 平台免下載、隨掃隨用的特性，結合政府 Open Data 與 AI 技術，提供即時、直覺的健康生活助手。"
    elif "特色" in user_message:
        return "🤖 系統三大特色：\n1. 即時同步政府開放資料\n2. AI 智慧語言模型互動\n3. 圖文選單一鍵操作"
    else:
        return f"🤖 AI 智慧助手收到您的訊息：「{user_message}」\n這是一個結合 LINE Bot 與 AI 的專案 Demo！我可以回答關於本專案的動機、架構，或是幫您分析氣候知識喔！"

# --- XỬ LÝ TIN NHẮN TỪ USER ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    
    # Lọc từ khóa linh hoạt hơn
    if any(keyword in user_msg for keyword in ["空氣", "天氣", "AQI", "台北", "台中", "高雄", "台南", "新竹"]):
        clean_msg = user_msg.replace("空氣", "").replace("天氣", "").replace("品質", "").strip()
        if not clean_msg:
            clean_msg = "台北"
        reply_text = get_taiwan_aqi(clean_msg)
    else:
        reply_text = call_ai_assistant(user_msg)
        
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
