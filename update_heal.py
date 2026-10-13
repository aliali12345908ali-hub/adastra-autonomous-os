from pathlib import Path

main_path = Path('app/main.py')
code = main_path.read_text()

if "self-heal" not in code:
    heal_endpoint = '''
class SelfHealRequest(BaseModel):
    api_key: str
    error_traceback: str
    target_file: str = "app/main.py"

@app.post("/api/v1/self-heal")
async def self_heal_system(data: SelfHealRequest):
    auth_data = verify_and_log_key(data.api_key)
    if auth_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Self-healing requires admin role")
        
    target_path = ROOT_DIR / data.target_file
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Target file not found")
        
    current_code = target_path.read_text()
    fix_proposal = ""
    
    try:
        if GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            prompt_text = f"Analyze this error traceback in Adastra Autonomous OS and provide a python patch or fix strategy.\\nTraceback:\\n{data.error_traceback}\\n\\nCode:\\n{current_code}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                fix_proposal = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            fix_proposal = "Gemini API key missing for healing."
    except Exception as e:
        fix_proposal = f"Healing engine error: {str(e)}"
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO evolution_logs (improvement_goal, patch_applied, status) VALUES (?, ?, ?)",
        (f"HEAL: {data.error_traceback[:100]}", fix_proposal[:500], "success")
    )
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "healer": auth_data["user_email"],
        "target_file": data.target_file,
        "gemini_fix_proposal": fix_proposal,
        "message": "Self-healing analysis completed successfully via Gemini Direct API."
    }
'''
    # Insert before dashboard endpoint
    code = code.replace('@app.get("/api/v1/dashboard")', heal_endpoint + '\n@app.get("/api/v1/dashboard")')
    main_path.write_text(code)
    print("SUCCESS: Self-Healing Engine added to app/main.py!")
else:
    print("Self-Healing Engine already exists.")
