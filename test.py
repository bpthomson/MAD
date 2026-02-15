from google import genai

# 初始化 Client
# 如果已設置環境變數 GOOGLE_API_KEY，則無需傳入參數
client = genai.Client(api_key="AIzaSyB_9TrLvZWs-DBZaAoNYbJ0yxEQNjdkSX4")

print("可用於生成內容的模型列表：")
# 使用 models.list() 取得模型清單
for m in client.models.list():
    # 過濾出支援 generateContent 操作的模型（即一般對話模型）
    if "generateContent" in m.supported_actions:
        print(f"模型名稱: {m.name}")
        print(f"描述: {m.description}")
        print("-" * 30)