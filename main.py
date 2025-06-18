import re
import os
import time
from tkinter import messagebox
import tkinter as tk
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
import datetime



EXCEL_FILE = os.path.join("data", "sample_price_tracker.xlsx")



def clean_price(price_text):
    price_number= re.sub(r"[^\d]","",price_text)
    
    if price_number:
        return int(price_number)
    else :
        None

def get_price_from_daraz(url):
    options = Options()
    options.add_argument("--ignore-certificate-errors")
    

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        price_tag = soup.find("span", attrs={"class": lambda c: c and "pdp-price" in c})
        if price_tag:
            price_text = price_tag.get_text()
            return clean_price(price_text)
        else:
            return None
    except Exception :
        return None
    finally:
        driver.quit()


def excelManager(file_path):
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    actual_prices = []
    statuses = []
    date = []
    time = []

    for _, row in df.iterrows():
        url = row["URL"]
        threshold = row["Threshold Price"]
        actual = get_price_from_daraz(url)
        actual_prices.append(actual)
        date.append(datetime.datetime.now().date())
        time.append(datetime.datetime.now().time().strftime("%H:%M"))

        if actual is None:
            statuses.append("Price Not Found")
        elif actual <= threshold:
            statuses.append("Below Target")
        else:
            statuses.append("Above Target")

    df["Actual Price"] = actual_prices
    df["Status"] = statuses
    df["Date "]=date
    df["Time"]=time

    with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="Sheet2", index=False)

    messagebox.showinfo("Success", "Scraping complete. Check Sheet2 in Excel file.")


def add_to_wishlist():
    product_name = product_name_entry.get().strip()
    url = url_entry.get().strip()
    date = datetime.datetime.now().date()
    
    
    try:

        threshold = int(threshold_entry.get())
        if threshold<0 or threshold==0:
            messagebox.showerror("Error","Threshold must be a positive value greater than 0.")
            threshold_entry.delete(0,tk.END)
            return False
        
    except ValueError:
        messagebox.showerror("Error", "Threshold must be a number.")
        return False
        

    if not url:
        messagebox.showerror("Error", "URL cannot be empty.")
        return

    if not product_name:
        messagebox.showerror("Error", "Product name cannot be empty.")
        return

    
    os.makedirs("data", exist_ok=True)   

    
    new_data = {
        "Product Name": [product_name],
        "URL": [url],
        "Threshold Price": [threshold],
        "Date":[date]
    }

    try:
        if os.path.exists(EXCEL_FILE):
            
            df = pd.read_excel(EXCEL_FILE, sheet_name="Sheet1")
            
            
            df.columns = df.columns.str.strip()
            expected_columns = ["Product Name", "URL", "Threshold Price"]
            
            
            if not all(col in df.columns for col in expected_columns):
                
                df = pd.DataFrame(columns=expected_columns)
            
            
            df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
        else:
            
            df = pd.DataFrame(new_data)

        
        with pd.ExcelWriter(
            
            EXCEL_FILE,
            engine='openpyxl',
            mode='w', 
        ) as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False)
            
        messagebox.showinfo("Success", "Item added to wishlist.")
        product_name_entry.delete(0, tk.END)
        url_entry.delete(0, tk.END)
        threshold_entry.delete(0, tk.END)

    except PermissionError:
        messagebox.showerror("Error", "Please close the Excel file before saving.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save data: {str(e)}")

def run_scraper():
        if not os.path.exists(EXCEL_FILE):
            messagebox.showerror("Error", "Wishlist Excel file not found.")
            return
        excelManager(EXCEL_FILE)


root = tk.Tk()
root.title("Daraz Price Tracker")
root.geometry("400x300")
root.configure(bg="#2c2c2c")

title = tk.Label(root, text="Daraz Price Tracker", font=("Arial", 16), fg="white", bg="#2c2c2c")
title.pack(pady=10)

tk.Label(root, text="Product Name:", bg="#2c2c2c", fg="white").pack()
product_name_entry = tk.Entry(root, width=40)
product_name_entry.pack(pady=3)

tk.Label(root, text="Product URL:", bg="#2c2c2c", fg="white").pack()
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=2)

tk.Label(root, text="Threshold Price:", bg="#2c2c2c", fg="white").pack()
threshold_entry = tk.Entry(root, width=20)
threshold_entry.pack(pady=2)

tk.Button(root, text="Add to Wishlist", command=add_to_wishlist, bg="#00aaff", fg="white").pack(pady=10)
tk.Button(root, text="Run Tracker", command=run_scraper, bg="#00cc66", fg="white").pack(pady=10)

root.mainloop()
