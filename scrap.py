from playwright.sync_api import sync_playwright
import csv
import time

# ========== CONFIG (EDIT THESE) ==========

BASE_URL = "https://ticketsearch.it.att.com"  # landing URL
TICKET_NUMBERS = [
    "CHG000010308769",  # example, add more if you want
]

OUTPUT_CSV = "aots_information_tab.csv"

# -----------------------------------------
# Selectors – you will likely need to adjust these using DevTools
# -----------------------------------------

# Left menu link for "Search Change Requests"
SEL_SEARCH_CHANGE_REQUESTS = "text=Search Change Requests"

# Input where you type the Change Request number
# Replace this with the real selector from DevTools if needed
SEL_TICKET_INPUT = "input[name='aotsCmTicket']"

# "Get Ticket" button
SEL_GET_TICKET_BUTTON = "input[type='button'][value*='Get Ticket']"

# If the Information tab needs to be clicked
SEL_INFORMATION_TAB = "text=Information"

# XPaths for fields inside Information tab
FIELD_SELECTORS = {
    "Category": "xpath=//td[normalize-space()='Category:']/following-sibling::td[1]",
    "Type": "xpath=//td[normalize-space()='Type:']/following-sibling::td[1]",
    "Item": "xpath=//td[normalize-space()='Item:']/following-sibling::td[1]",
    "ChangeRequestNumber": "xpath=//td[contains(normalize-space(),'Change Request Number')]/following-sibling::td[1]",
    "ApprovalStatus": "xpath=//td[normalize-space()='Approval Status:']/following-sibling::td[1]",
    "Status": "xpath=//td[normalize-space()='Status:']/following-sibling::td[1]",
    "Urgency": "xpath=//td[normalize-space()='Urgency:']/following-sibling::td[1]",
    "ClosureCode": "xpath=//td[contains(normalize-space(),'Closure Code')]/following-sibling::td[1]",
    "Sequence": "xpath=//td[normalize-space()='Sequence:']/following-sibling::td[1]",
    "Summary": "xpath=//td[normalize-space()='Summary:']/following-sibling::td[1]",
    "Description": "xpath=//td[normalize-space()='Description:']/following-sibling::td[1]",
    "RequesterName": "xpath=//td[contains(normalize-space(),'Requester Name')]/following-sibling::td[1]",
    "RequesterLogin": "xpath=//td[contains(normalize-space(),'Requester Login')]/following-sibling::td[1]",
    "RequesterEmail": "xpath=//td[contains(normalize-space(),'Requester Email')]/following-sibling::td[1]",
    "RequesterPhone": "xpath=//td[contains(normalize-space(),'Requester Phone')]/following-sibling::td[1]",
}

# ========== END CONFIG ==========


def get_text_safe(page, selector: str) -> str:
    """Return trimmed text for first match, or empty string."""
    loc = page.locator(selector)
    try:
        if loc.count() == 0:
            return ""
        txt = loc.first.text_content()
        if txt is None:
            return ""
        return txt.strip()
    except Exception:
        return ""


def main():
    with sync_playwright() as p:
        # Launch headed browser so you can see it and login
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to base URL and let you login manually
        page.goto(BASE_URL, wait_until="load")
        print("➡️ Browser opened. Log in with SSO / VPN etc in the window.")
        input("When the Ticket Search home page is fully loaded, press ENTER here...")

        all_rows = []

        for ticket in TICKET_NUMBERS:
            print(f"\n=== Processing ticket {ticket} ===")

            # 2. Click "Search Change Requests" in left menu
            page.click(SEL_SEARCH_CHANGE_REQUESTS)
            page.wait_for_timeout(1000)

            # 3. Fill ticket number and click "Get Ticket"
            page.wait_for_selector(SEL_TICKET_INPUT)
            page.fill(SEL_TICKET_INPUT, ticket)

            page.click(SEL_GET_TICKET_BUTTON)

            # 4. Wait for information page to load
            # adjust this selector to something that appears only on ticket page
            page.wait_for_timeout(3000)  # simple wait; can be improved later

            # 5. Click Information tab if needed
            try:
                page.click(SEL_INFORMATION_TAB)
                page.wait_for_timeout(1000)
            except Exception:
                # maybe already on Information
                pass

            # 6. Extract fields from Information tab
            row = {"TicketNumber": ticket}
            for field_name, selector in FIELD_SELECTORS.items():
                value = get_text_safe(page, selector)
                row[field_name] = value

            all_rows.append(row)
            print("Extracted:")
            for k, v in row.items():
                print(f"  {k}: {v}")

        # 7. Save CSV
        if all_rows:
            fieldnames = list(all_rows[0].keys())
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"\n📁 Saved {len(all_rows)} ticket(s) to {OUTPUT_CSV}")

        input("Press ENTER to close browser...")
        browser.close()


if __name__ == "__main__":
    main()