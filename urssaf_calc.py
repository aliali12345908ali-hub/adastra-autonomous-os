import os

def calculate_urssaf():
    # حساب الإجمالي المدفوع
    paid_file = "paid_invoices.txt"
    paid_count = 0
    if os.path.exists(paid_file):
        with open(paid_file, "r") as f:
            paid_count = len([line for line in f if line.strip()])

    total_gross = paid_count * 870.0 # الإجمالي الحالي 3480 EUR
    
    # نسبة اقتطاع URSSAF لخدمات BNC (حوالي 21.2%)
    urssaf_rate = 0.212
    urssaf_amount = total_gross * urssaf_rate
    net_income = total_gross - urssaf_amount

    print("\n==================================================")
    print("       ADASTRA OS - CALCULATEUR URSSAF & IMPÔTS   ")
    print("==================================================")
    print(f"💶 Chiffre d'Affaires Brut (Total) : {total_gross:.2f} EUR")
    print(f"🏛️ Cotisations Sociales URSSAF (~21.2%): {urssaf_amount:.2f} EUR")
    print(f"📌 Régime TVA                     : Non Applicable (Art. 293 B CGI)")
    print("--------------------------------------------------")
    print(f"💰 Revenu Net Estimé (Dans votre poche) : {net_income:.2f} EUR")
    print("==================================================\n")

if __name__ == "__main__":
    calculate_urssaf()
