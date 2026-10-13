from pathlib import Path

main_path = Path('app/main.py')
code = main_path.read_text()

# Check if run-shell already exists
if "run-shell" not in code:
    # We will append the new endpoint before dashboard or at the end
    new_endpoint = '''
class ShellCommandRequest(BaseModel):
    api_key: str
    command: str

@app.post("/api/v1/run-shell")
async def run_local_shell(data: ShellCommandRequest):
    import subprocess
    auth_data = verify_and_log_key(data.api_key)
    
    # Restrict dangerous system commands if needed, or allow full control for admin
    if auth_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Shell execution requires admin role")
        
    try:
        process = subprocess.run(
            data.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = process.stdout if process.returncode == 0 else process.stderr
    except Exception as e:
        output = str(e)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO execution_logs (user_email, command, status) VALUES (?, ?, ?)",
        (auth_data["user_email"], f"SHELL: {data.command}", "success")
    )
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "executor": auth_data["user_email"],
        "command": data.command,
        "output": output.strip()
    }
'''
    # Insert before dashboard endpoint
    code = code.replace('@app.get("/api/v1/dashboard")', new_endpoint + '\n@app.get("/api/v1/dashboard")')
    main_path.write_text(code)
    print("SUCCESS: Local Shell Executor added to app/main.py!")
else:
    print("Local Shell Executor already exists.")
