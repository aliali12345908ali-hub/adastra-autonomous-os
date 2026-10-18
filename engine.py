import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_automated_invoice(client_name, amount, seq_num):
    invoice_number = f"ADASTRA-2026-{seq_num:03d}"
    filename = f"facture_{invoice_number}.pdf"
    
    # مسار الحفظ المباشر إلى التنزيلات في الهاتف
    output_path = os.path.join("/sdcard/Download", filename)
    
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # تفاصيل الفاتورة الرسمية
    c.drawString(50, 750, "FACTURE / INVOICE (Automated System)")
    c.drawString(50, 730, f"Numéro : {invoice_number}")
    c.drawString(50, 715, f"Date : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # بياناتك القانونية (Micro-entrepreneur)
    c.drawString(50, 670, "Prestataire : MR ABDALLAH BEN BELGACEM")
    c.drawString(50, 655, "Statut : Micro-entrepreneur")
    c.drawString(50, 640, "TVA non applicable, art. 293 B du CGI")
    
    # بيانات العميل والمبلغ
    c.drawString(50, 600, f"Client : {client_name}")
    c.drawString(50, 550, "Description : Prestation de services & Automatisation IA")
    c.drawString(50, 535, f"Total à payer : {amount:.2f} EUR")
    
    # بيانات الـ RIB البنكي (Nickel)
    c.drawString(50, 480, "Coordonnées bancaires pour le virement (RIB Nickel) :")
    c.drawString(50, 465, "Titulaire : MR ABDALLAH BEN BELGACEM")
    c.drawString(50, 450, "IBAN : FR76 1659 8000 0140 0014 2630 322")
    c.drawString(50, 435, "BIC/Swift : FPELFR21XXX")
    
    c.save()
    print(f"[AUTO-ENGINE] Facture générée : {filename}")

if __name__ == "__main__":
    if os.path.exists("clients.txt"):
        with open("clients.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines, start=1):
            parts = line.strip().split(",")
            if len(parts) == 2:
                c_name = parts[0].strip()
                c_amount = float(parts[1].strip())
                generate_automated_invoice(c_name, c_amount, i)
        print("[+] Toutes les factures ont été générées et exportées vers /sdcard/Download/ avec succès !")
    else:
        print("[-] Erreur : Le fichier clients.txt est introuvable.")


