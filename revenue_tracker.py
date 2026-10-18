import os

INVOICES = {
    "ADASTRA-2026-001": {"client": "Parisian AI Systems SARL", "amount": 900.00},
    "ADASTRA-2026-002": {"client": "European Digital Solutions BV", "amount": 1020.00},
    "ADASTRA-2026-003": {"client": "Global Logistics France SAS", "amount": 540.00},
    "ADASTRA-2026-004": {"client": "Brussels Secure Cloud BV", "amount": 1020.00},
}

PAID_FILE = "paid_invoices.txt"

TRANSLATIONS = {
    "FR": {
        "title": "ADASTRA AUTONOMOUS OS - TABLEAU DE BORD",
        "projected": "Chiffre d'Affaires Projeté",
        "realized": "Chiffre d'Affaires Réel (Nickel)",
        "status_paid": "PAYÉ (Reçu sur Nickel)",
        "status_pending": "EN ATTENTE DE VIREMENT",
        "menu_1": "1. Afficher le résumé des revenus",
        "menu_2": "2. Valider la réception d'un virement SEPA",
        "menu_3": "3. Changer la langue / Switch Language",
        "enter_inv": "Entrez le numéro de la facture payée (ex: ADASTRA-2026-001): ",
        "success": "Facture marquée comme PAYÉE avec succès !",
        "already": "Cette facture est déjà marquée comme payée.",
        "not_found": "Numéro de facture introuvable."
    },
    "EN": {
        "title": "ADASTRA AUTONOMOUS OS - REVENUE DASHBOARD",
        "projected": "Total Projected Revenue",
        "realized": "Realized Revenue (Nickel Account)",
        "status_paid": "PAID (Received on Nickel)",
        "status_pending": "PENDING PAYMENT",
        "menu_1": "1. Show Revenue Summary",
        "menu_2": "2. Confirm SEPA Transfer Received",
        "menu_3": "3. Change Language",
        "enter_inv": "Enter paid invoice ID (e.g. ADASTRA-2026-001): ",
        "success": "Invoice successfully marked as PAID!",
        "already": "Invoice is already marked as paid.",
        "not_found": "Invoice ID not found."
    }
}

CURRENT_LANG = "FR"

def load_paid():
    if not os.path.exists(PAID_FILE):
        return []
    with open(PAID_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_paid(paid_list):
    with open(PAID_FILE, "w") as f:
        for item in paid_list:
            f.write(f"{item}\n")

def show_summary():
    t = TRANSLATIONS[CURRENT_LANG]
    paid_list = load_paid()
    total_projected = sum(inv["amount"] for inv in INVOICES.values())
    total_realized = sum(INVOICES[inv_id]["amount"] for inv_id in paid_list if inv_id in INVOICES)
    
    print("\n==================================================")
    print(f"       {t['title']}")
    print("==================================================")
    print(f"{t['projected']}: {total_projected:.2f} EUR")
    print(f"{t['realized']}: {total_realized:.2f} EUR")
    print("--------------------------------------------------")
    print("Détails des Factures :")
    for inv_id, info in INVOICES.items():
        status = f"[ {t['status_paid']} ]" if inv_id in paid_list else f"[ {t['status_pending']} ]"
        print(f" - {inv_id} ({info['client']}): {info['amount']:.2f} EUR --> {status}")
    print("==================================================\n")

def mark_as_paid():
    t = TRANSLATIONS[CURRENT_LANG]
    show_summary()
    inv_id = input(t["enter_inv"]).strip()
    if inv_id in INVOICES:
        paid_list = load_paid()
        if inv_id not in paid_list:
            paid_list.append(inv_id)
            save_paid(paid_list)
            print(f"\n[+] {t['success']}")
        else:
            print(f"\n[-] {t['already']}")
    else:
        print(f"\n[-] {t['not_found']}")

def main():
    global CURRENT_LANG
    while True:
        t = TRANSLATIONS[CURRENT_LANG]
        print(f"--- Langue Actuelle / Current Language : {CURRENT_LANG} ---")
        print(t["menu_1"])
        print(t["menu_2"])
        print(t["menu_3"])
        print("4. Quitter / Exit")
        
        choice = input("\nSélectionnez une option (1-4): ").strip()
        if choice == "1":
            show_summary()
        elif choice == "2":
            mark_as_paid()
        elif choice == "3":
            CURRENT_LANG = "EN" if CURRENT_LANG == "FR" else "FR"
            print(f"\n[+] Langue changée vers : {CURRENT_LANG}\n")
        elif choice == "4":
            print("\nFermeture du système ADASTRA. À bientôt !\n")
            break

if __name__ == "__main__":
    main()
