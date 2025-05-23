import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL    = "https://lrs.telangana.gov.in/layouts/Citizen_Downloads.aspx"
OUTPUT_CSV  = "E:/lrs_3rd_series.csv"
#series start and end numbers
START       = 1
END         = 1805 
THREADS     = 5


fieldnames = [
    "Application No", "Name", "Father Name", "Mobile",
    "Survey No", "Plot No", "Layout/Plot",
    "Status", "Fee Status", "Fee Payment"
]


def get_headless_driver():
    #headless mode options
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def process_application(i):
    app_no = f"G/XYZ/{i:06d}/2020" #change accordingly to match series 
    try:
        driver = get_headless_driver()
        wait = WebDriverWait(driver, 10)
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
            print(f"❌ Skipped (No header): {app_no}")
            return None

        headers = [h.text.strip() for h in header_cells]
        data_rows = tbl.find_elements(By.XPATH, ".//tbody/tr[position()>1]")
        if not data_rows:
            print(f"❌ Skipped (No data): {app_no}")
            return None

        row = data_rows[0]
        cells = row.find_elements(By.TAG_NAME, "td")
        row_data = {}
        for idx, head in enumerate(headers):
            if head.lower().startswith("document") or head.lower().startswith("receipt"):
                continue
            row_data[head] = cells[idx].text.strip() if idx < len(cells) else ""

        result = {
            "Application No": app_no,
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

        print(f"✅ Success: {app_no}")
        return result

    except Exception as e:
        print(f"❌ Skipped ({type(e).__name__}): {app_no}")
        return None

    finally:
        try:
            driver.quit()
        except:
            pass

#main driver code
if __name__ == "__main__":
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = [executor.submit(process_application, i) for i in range(START, END + 1)]

            for future in as_completed(futures):
                data = future.result()
                if data:
                    writer.writerow(data)
