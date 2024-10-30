import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv('./data.csv', encoding='cp949', low_memory=False)

df = df.drop(columns=['Unnamed: 0', 'line', 'name', 'mold_name', 'emergency_stop'])
df = df.drop(index=19327)
df = df.rename(columns={'date': 'temp_date', 'time': 'date'}).rename(columns={'temp_date': 'time'})

# 결측치 처리
molten_filtered = df['molten_volume'].loc[~df['molten_volume'].isin([0, 2767])].dropna()
molten_median = molten_filtered.median()
df['molten_volume'] = df['molten_volume'].fillna(molten_median)
df['molten_temp'] = df['molten_temp'].interpolate(method='linear')
df.loc[0:699, 'lower_mold_temp3'] = df['lower_mold_temp3'].fillna(1449)
df.loc[0:699, 'upper_mold_temp3'] = df['upper_mold_temp3'].interpolate(method='linear')
df['tryshot_signal'] = df['tryshot_signal'].map({'D': 1}).fillna(0)
df['heating_furnace'] = df['heating_furnace'].map({'A': 1, 'B': 2}).fillna(0)
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')

# mold code
mold_codes = {
    '8917': df[df['mold_code'] == 8917],
    '8412': df[df['mold_code'] == 8412],
    '8722': df[df['mold_code'] == 8722],
    '8573': df[df['mold_code'] == 8573],
    '8413': df[df['mold_code'] == 8413],
    '8600': df[df['mold_code'] == 8600],
    '8576': df[df['mold_code'] == 8576]
}

# streamlit
st.title("Dynamic Data Plotting")
adf_key = st.selectbox("Choose mold_code:", options=mold_codes.keys())
adf = mold_codes[adf_key]

column_data = st.selectbox("Select column to plot:", options=adf.columns)
start_date = st.date_input("Start Date:", value=pd.to_datetime("2019-01-01"))
end_date = st.date_input("End Date:", value=pd.to_datetime("2019-04-01"))

filtered_data = adf[(adf['datetime'] >= pd.to_datetime(start_date)) & (adf['datetime'] <= pd.to_datetime(end_date))]

if not filtered_data.empty:
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])
    unique_days = filtered_data['date'].dt.date.unique()

    fig, ax = plt.subplots(figsize=(12, 8))
    for day in unique_days:
        daily_data = filtered_data[filtered_data['date'].dt.date == day].copy()
        daily_data['time'] = pd.to_datetime(daily_data['time'], format='%H:%M:%S', errors='coerce').dt.time
        daily_data['time'] = pd.to_timedelta(daily_data['time'].astype(str))
        ax.plot(daily_data['time'].dt.total_seconds() / 3600, daily_data[column_data], label=str(day))

    ax.set_facecolor("black")
    ax.set_title(f"{column_data} Over Each Day ({start_date} to {end_date})", color="black")
    ax.set_xlabel("Time (Hours)", color="black")
    ax.set_ylabel(column_data, color="black")
    ax.set_xticks(range(0, 25))
    ax.grid(color='gray', linestyle='--', linewidth=0.5)
    ax.legend(title="Date", loc="upper left", bbox_to_anchor=(1, 1), title_fontsize='small', fontsize='small', labelcolor='black')

    st.pyplot(fig)
else:
    st.warning("No data available for the selected date range.")
