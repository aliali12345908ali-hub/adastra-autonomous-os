from pathlib import Path

main_path = Path('app/main.py')
code = main_path.read_text()

if "translate" not in code:
    translate_endpoint = '''
class TranslateRequest(BaseModel):
    api_key: str
    text: str
    target_language: str = "Arabic"

@app.post("/api/v1/translate")
async def translate_text(data: TranslateRequest):
    auth_data = verify_and_log_key(data.api_key)
    
    translated_text = ""
    try:
        if GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            prompt_text = f"Translate the following text accurately to {data.target_language}. Return only the translated text without extra conversational filler:\\n\\n{data.text}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                translated_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            translated_text = "Gemini API key missing for translation."
    except Exception as e:
        translated_text = f"Translation error: {str(e)}"
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO execution_logs (user_email, command, status) VALUES (?, ?, ?)",
        (auth_data["user_email"], f"TRANSLATE to {data.target_language}", "success")
    )
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "translator": auth_data["user_email"],
        "target_language": data.target_language,
        "original_text": data.text,
        "translated_text": translated_text
    }
'''
    # Insert before dashboard endpoint
    code = code.replace('@app.get("/api/v1/dashboard")', translate_endpoint + '\n@app.get("/api/v1/dashboard")')
    main_path.write_text(code)
    print("SUCCESS: Translation Engine added to app/main.py!")
else:
    print("Translation Engine already exists.")
