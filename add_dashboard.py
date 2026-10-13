from pathlib import Path

path = Path("app/main.py")
code = path.read_text(encoding="utf-8")

dashboard_code = '''
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def adastra_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Adastra Autonomous OS - Dashboard</title>
        <style>
            body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }
            .container { max-width: 800px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            h1 { color: #38bdf8; text-align: center; }
            .card { background: #334155; padding: 15px; margin: 15px 0; border-radius: 8px; }
            button { background: #0284c7; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0369a1; }
            pre { background: #0f172a; padding: 10px; border-radius: 5px; overflow-x: auto; color: #34d399; }
            input { width: 70%; padding: 8px; border-radius: 5px; border: 1px solid #64748b; background: #0f172a; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Adastra Autonomous OS</h1>
            <p style="text-align: center;">المالك: <strong>MR ABDALLAH BEN BELGACEM</strong></p>
            
            <div class="card">
                <h3>حالة النظام والمالية</h3>
                <button onclick="fetchFinance()">جلب البيانات المالية</button>
                <pre id="finance-result">انقر على الزر لعرض التفاصيل...</pre>
            </div>
            
            <div class="card">
                <h3>المساعد الذكي (AI Agent)</h3>
                <input type="text" id="ai-prompt" placeholder="اكتب أمرك هنا...">
                <button onclick="sendAI()">إرسال</button>
                <pre id="ai-result">نتيجة الذكاء الاصطناعي ستظهر هنا...</pre>
            </div>
        </div>

        <script>
            async function fetchFinance() {
                const res = await fetch("/api/v1/finance");
                const data = await res.json();
                document.getElementById("finance-result").innerText = JSON.stringify(data, null, 2);
            }
            async function sendAI() {
                const prompt = document.getElementById("ai-prompt").value;
                const res = await fetch("/api/v1/ai", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                document.getElementById("ai-result").innerText = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """
    return html_content
'''

if "response_class=HTMLResponse" not in code:
    with open("app/main.py", "a", encoding="utf-8") as f:
        f.write("\n" + dashboard_code)
    print("Step 4 (Web Dashboard) integrated successfully!")
else:
    print("Dashboard endpoint already exists.")
