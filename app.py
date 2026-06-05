import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 1. Điền các thông tin bảo mật từ LINE của nhóm em vào đây
# (Hoặc cấu hình trong Environment Variables trên Render)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'ĐIỀN_TOKEN_SIÊU_DÀI_CỦA_EM_VÀO_ĐÂY')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'ĐIỀN_CHANNEL_SECRET_CỦA_EM_VÀO_ĐÂY')

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

# --- HÀM GỌI API THỜI TIẾT & AQI CHÍNH PHỦ ĐÀI LOAN ---
def get_taiwan_aqi(location_name):
    try:
        # API URL lấy dữ liệu AQI thực tế của Bộ Môi trường Đài Loan (MOENV)
        url = "https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3de7ef334c1&limit=1000&sort=ImportDate%20desc&format=JSON"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        for record in data.get('records', []):
            if location_name in record.get('sitename', '') or location_name in record.get('county', ''):
                site = record.get('sitename')
                county = record.get('county')
                aqi = int(record.get('aqi', 0))
                status = record.get('status')
                pm25 = record.get('pm2.5', '無資料')
                
                # Logic phân tích và đưa ra lời khuyên đeo khẩu trang
                if aqi <= 50:
                    advice = "🟢 空氣良好，免戴口罩 (Không khí tốt, miễn đeo khẩu trang)."
                elif aqi <= 100:
                    advice = "🟡 空氣普通，敏感族群出門建議配戴口罩 (Không khí bình thường, nhóm nhạy cảm nên đeo)."
                else:
                    advice = "🔴 空氣不良，出門請務必配戴口罩！(Không khí ô nhiễm, bắt buộc đeo khẩu trang!)"
                
                return f"📍 觀測站: {county} - {site}\n😷 AQI 指數: {aqi} ({status})\n🔹 PM2.5: {pm25} μg/m³\n💡 健康建議: {advice}"
                
        return f"找不到「{location_name}」的空氣品質觀測資料，請輸入正確的台灣縣市或測站名稱（例如：台北、西屯）。"
    except Exception as e:
        return "系統 busy，請稍後再試！"

# --- HÀM GỌI AI ĐỂ TRẢ LỜI CÂU HỎI TỰ DO ---
def call_ai_assistant(user_message):
    # Đây là nơi tích hợp mô hình ngôn ngữ lớn (AI LLM) để phản hồi thông minh
    # Đoạn này giả lập phản hồi của AI trợ lý đồ án
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
    
    # Nếu tin nhắn chứa từ khóa liên quan đến thời tiết/không khí -> Gọi API chính phủ
    if any(keyword in user_msg for keyword in ["空氣", "天氣", "AQI", "台北", "台中", "高雄", "台南", "新竹"]):
        # Trích xuất tên khu vực để tìm kiếm (mặc định lấy luôn tin nhắn text)
        clean_msg = user_msg.replace("空氣", "").replace("天氣", "").replace("品質", "").strip()
        if not clean_msg:
            clean_msg = "台北" # Mặc định nếu gõ chung chung
        reply_text = get_taiwan_aqi(clean_msg)
    else:
        # Nếu hỏi câu hỏi khác -> Đá qua cho AI trả lời
        reply_text = call_ai_assistant(user_msg)
        
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
