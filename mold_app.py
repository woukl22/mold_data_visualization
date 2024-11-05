import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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

mold_codes = {f"{code} ({len(df[df['mold_code'] == code])})": df[df['mold_code'] == code]
              for code in df['mold_code'].unique()}

st.sidebar.title("Data Selection")
adf_key = st.sidebar.selectbox("Mold Code:", options=list(mold_codes.keys()))
adf = mold_codes[adf_key]

excluded_columns = ['date', 'time', 'working', 'count', 'datetime', 'registration_time', 'tryshot_signal', 'mold_code', 'heating_furnace']
available_columns = [col for col in adf.columns if col not in excluded_columns]

num_charts = st.sidebar.selectbox("Number of Line Charts:", options=[1, 2, 3, 4], index=0)

start_date = st.sidebar.date_input("Start Date:", value=pd.to_datetime("2019-01-01"))
end_date = st.sidebar.date_input("End Date:", value=pd.to_datetime("2019-04-01"))

filtered_data = adf[(adf['datetime'] >= pd.to_datetime(start_date)) & (adf['datetime'] <= pd.to_datetime(end_date))]

st.title("Mold Data Visualization")

if not filtered_data.empty:
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])
    unique_days = filtered_data['date'].dt.date.unique()
    
    # 라인차트
    if num_charts == 1:
        cols = [st.container()]
    elif num_charts == 2:
        cols = st.columns(2)
    elif num_charts == 3:
        cols = st.columns(3)
    else:
        cols = [st.columns(2), st.columns(2)]

    for i in range(num_charts):
        if num_charts == 4:
            col = cols[i // 2][i % 2]
        else:
            col = cols[i]

        with col:
            column = st.selectbox(f"Select Column for Line Chart {i + 1}:", options=available_columns, key=f"chart_{i + 1}")
            
            fig = go.Figure()
            for day in unique_days:
                daily_data = filtered_data[filtered_data['date'].dt.date == day].copy()
                daily_data['time'] = pd.to_datetime(daily_data['time'], format='%H:%M:%S', errors='coerce').dt.time
                daily_data['time'] = pd.to_timedelta(daily_data['time'].astype(str))
                fig.add_trace(go.Scatter(x=daily_data['time'].dt.total_seconds() / 3600, y=daily_data[column],
                                         mode='lines', name=str(day)))

            fig.update_layout(
                title=f"{column} Over Each Day ({start_date} to {end_date})",
                xaxis_title="Time (Hours)",
                yaxis_title=column,
                legend_title="Date",
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="white")
            )

            st.plotly_chart(fig, use_container_width=True)

    # 상관관계 히트맵
    st.subheader("Correlation Heatmap")
    numeric_columns = adf[available_columns].select_dtypes(include=[np.number]).columns
    corr = adf[numeric_columns].corr()

    fig = px.imshow(corr, text_auto=".2f", aspect="auto", title="Correlation Heatmap")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available for the selected date range.")
