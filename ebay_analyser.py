import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

st.title("eBay Used Electronics Deal Analyzer")

uploaded_file = st.file_uploader("Upload an eBay HTML page", type=["html"])

if uploaded_file:
    soup = BeautifulSoup(uploaded_file, 'html.parser')
    items = soup.select('.s-item')

    listings = []
    for item in items:
        title_tag = item.select_one('.s-item__title')
        price_tag = item.select_one('.s-item__price')
        condition_tag = item.select_one('.SECONDARY_INFO')
        link_tag = item.select_one('a.s-item__link')

        title = title_tag.get_text(strip=True) if title_tag else ''
        price = price_tag.get_text(strip=True) if price_tag else ''
        condition = condition_tag.get_text(strip=True) if condition_tag else ''
        link = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''

        if title and price and "shop on ebay" not in title.lower():
            listings.append({
                'Title': title,
                'Price': price,
                'Condition': condition,
                'Link': link
            })

    df = pd.DataFrame(listings)
    st.success(f"{len(df)} listings found.")
    st.dataframe(df)
