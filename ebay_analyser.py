
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import re
from difflib import get_close_matches

st.title("eBay Used PC Deal Analyzer")

uploaded_current = st.file_uploader("Upload a current listing HTML page", type=["html"], key="current")
uploaded_sold = st.file_uploader("Upload a sold listings HTML page", type=["html"], key="sold")
uploaded_individual = st.file_uploader("Upload a full product page HTML", type=["html"], key="individual")
manual_price = st.number_input("If the listing page doesn't show the price, enter it manually (£)", min_value=0.0, value=100.0)

def parse_price(price_str):
    try:
        price = re.findall(r"\d+(?:\.\d+)?", price_str.replace(',', ''))
        return float(price[0]) if price else None
    except:
        return None

repair_keywords = {
    "no hdd": 15,
    "no hard drive": 15,
    "missing hdd": 15,
    "no ssd": 20,
    "missing ssd": 20,
    "no ram": 20,
    "missing ram": 20,
    "no gpu": 80,
    "no graphics card": 80,
    "doesn't boot": 30,
    "won't turn on": 40,
    "no power": 30,
    "no os": 0,
    "no windows": 0,
}

EBAY_FEE_PERCENTAGE = 0.128

def extract_sold_data(soup):
    items = soup.select('.s-item')
    sold = []
    for item in items:
        title_tag = item.select_one('.s-item__title')
        price_tag = item.select_one('.s-item__price')
        if title_tag and price_tag and "shop on ebay" not in title_tag.text.lower():
            sold.append({
                "Title": title_tag.text.strip(),
                "Price": parse_price(price_tag.text)
            })
    return pd.DataFrame(sold)

def estimate_repair_cost(desc):
    desc = desc.lower()
    total, reasons = 0, []
    for k, v in repair_keywords.items():
        if k in desc:
            total += v
            reasons.append(f"{k} (£{v})")
    return total, "; ".join(reasons) if reasons else "None"

if uploaded_sold and uploaded_individual:
    sold_soup = BeautifulSoup(uploaded_sold, 'html.parser')
    sold_df = extract_sold_data(sold_soup)

    ind_soup = BeautifulSoup(uploaded_individual, 'html.parser')
    title_tag = ind_soup.find('h1')
    desc_container = ind_soup.find('div', {'id': 'viTabs_0_is'}) or ind_soup.find('div', {'id': 'desc_div'})
    title = title_tag.get_text(strip=True) if title_tag else "N/A"
    desc = desc_container.get_text(separator=" ", strip=True) if desc_container else "N/A"

    matches = get_close_matches(title, sold_df['Title'], n=3, cutoff=0.3)
    matched_prices = sold_df[sold_df['Title'].isin(matches)]['Price']
    resale = matched_prices.mean() if not matched_prices.empty else None

    repair_cost, repair_reason = estimate_repair_cost(desc)
    listed_price = manual_price
    if resale:
        fee = resale * EBAY_FEE_PERCENTAGE
        profit = resale - listed_price - repair_cost - fee
        margin = profit / listed_price if listed_price else 0
    else:
        fee = profit = margin = None

    if profit is None:
        recommendation = "❓ Insufficient Data"
    elif profit > 30 and margin > 0.25:
        recommendation = "✅ Buy"
    elif profit > 0:
        recommendation = "⚠️ Watch"
    else:
        recommendation = "❌ Skip"

    results = pd.DataFrame([{
        "Title": title,
        "Estimated Resale (£)": round(resale, 2) if resale else "N/A",
        "Repair Cost (£)": repair_cost,
        "Repair Reason": repair_reason,
        "Estimated eBay Fee (£)": round(fee, 2) if fee else "N/A",
        "Estimated Profit (£)": round(profit, 2) if profit else "N/A",
        "Profit Margin (%)": f"{round(margin * 100, 1)}%" if margin else "N/A",
        "Recommendation": recommendation
    }])
    st.subheader("Analysis Result")
    st.dataframe(results)
