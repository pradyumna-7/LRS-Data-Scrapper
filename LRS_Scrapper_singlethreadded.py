from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

# — CONFIG —
BASE_URL      = "https://lrs.telangana.gov.in/layouts/Citizen_Downloads.aspx"
OUTPUT_CSV    = "lrs_data.csv"
START         = 1
END           = 600
SERIES_END    = 600   # track “missing” over the full range

driver = webdriver.Chrome()
wait   = WebDriverWait(driver, 10)

fieldnames = [
    "Application No", "Name", "Father Name", "Mobile",
    "Survey No", "Plot No", "Layout/Plot",
    "Status", "Fee Status", "Fee Payment"
]
found_apps   = []
missing_apps = []

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
    writer.writeheader()

    for i in range(START, END + 1):
        app_no = f"G/XYZ/{i:06d}/2020" #change according to series
        try:
            driver.get(BASE_URL)
            wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_rbtnappnum_0"))).click()
            inp = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_txtappno")))
            inp.clear()
            inp.send_keys(app_no)

            btn = driver.find_element(By.ID, "ContentPlaceHolder1_btn_submit")
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            driver.execute_script("arguments[0].click();", btn)

            time.sleep(1)
            tbl = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_gvDownloadsData")))

            header_cells = tbl.find_elements(By.XPATH, ".//tbody/tr[1]/th")
            if not header_cells:
                raise Exception("No header row found")

            headers = [h.text.strip() for h in header_cells]

            data_rows = tbl.find_elements(By.XPATH, ".//tbody/tr[position()>1]")
            if not data_rows:
                raise Exception("No data rows")

            row = data_rows[0]
            cells = row.find_elements(By.TAG_NAME, "td")

            row_data = {}
            for idx, head in enumerate(headers):
                if head.lower().startswith("document") or head.lower().startswith("receipt"):
                    continue
                row_data[head] = cells[idx].text.strip() if idx < len(cells) else ""

            result = {
                "Application No": row_data.get("Application Number", ""),
                "Name":           row_data.get("Name", ""),
                "Father Name":    row_data.get("Father Name", ""),
                "Mobile":         row_data.get("Mobile Number", ""),
                "Survey No":      row_data.get("Survey No", ""),
                "Plot No":        row_data.get("Plot No", ""),
                "Layout/Plot":    row_data.get("Layout/Plot", ""),
                "Status":         row_data.get("Application Present Stage", ""),
                "Fee Status":     row_data.get("Fee Status", ""),
                "Fee Payment":    row_data.get("Fee Payment", ""),
            }

            writer.writerow(result)
            found_apps.append(i)
            print(f"✅ {app_no}")

        except Exception:
            missing_apps.append(i)
            print(f"❌ {app_no} skipped")


driver.quit()
print(f"Scraped : {len(found_apps)}")
print(f"Skipped : {len(missing_apps)}")
print("Missing list:", [f"{n:06d}" for n in missing_apps])
