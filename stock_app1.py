import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data
def load_data():
    return pd.read_csv("15 Years Stock Data of NVDA AAPL MSFT GOOGL and AMZN.csv", parse_dates=['Date'])

data = load_data()

# =====================================
# Сайдбар с 7 контролами
# =====================================
st.sidebar.header("🎚️ Панель управления")

# 1. Мультиселект компаний с иконками
companies = st.sidebar.multiselect(
    "📌 Выберите компании:",
    options=['AAPL', 'AMZN', 'GOOGL', 'MSFT', 'NVDA'],
    default=['AAPL', 'NVDA'],
    format_func=lambda x: {
        'AAPL': '🍎 Apple',
        'AMZN': '📦 Amazon', 
        'GOOGL': '🔍 Google',
        'MSFT': '🖥️ Microsoft',
        'NVDA': '🎮 NVIDIA'
    }[x]
)

# 2. Селектор временного масштаба
time_resolution = st.sidebar.selectbox(
    "⏳ Гранулярность данных:",
    options=['Дни', 'Недели', 'Месяцы'],
    index=0,
    help="Агрегация данных по временным интервалам"
)

# 3. Ползунок для порога цены
price_threshold = st.sidebar.slider(
    "💰 Порог цены:",
    min_value=0,
    max_value=int(data[[f'Close_{c}' for c in companies]].max().max()),
    value=150,
    help="Отметка для визуализации ключевых уровней"
)

# 4. Переключатель типа графика
chart_type = st.sidebar.radio(
    "📊 Тип графика:",
    options=['Линия', 'Свечи', 'Область'],
    horizontal=True,
    index=0
)

# 5. Фильтр дней недели
days_of_week = st.sidebar.multiselect(
    "📅 Дни недели:",
    options=['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    default=['Пн', 'Вт', 'Ср', 'Чт', 'Пт'],
    help="Фильтрация по торговым дням"
)

# 6. Настройки отображения
show_legend = st.sidebar.checkbox("👁️ Показывать легенду", True)
show_hover = st.sidebar.checkbox("🔍 Подсказки при наведении", True)

# 7. Селектор технического индикатора
indicator = st.sidebar.selectbox(
    "📈 Технический индикатор:",
    options=['Нет', 'SMA (20)', 'EMA (50)', 'RSI (14)'],
    index=0
)

# =====================================
# Обработка данных
# =====================================
# Агрегация данных по выбранному масштабу
df = data.set_index('Date')
if time_resolution == 'Недели':
    df = df.resample('W').last()
elif time_resolution == 'Месяцы':
    df = df.resample('M').last()

# Фильтрация по дням недели
day_mapping = {'Пн': 0, 'Вт': 1, 'Ср': 2, 'Чт': 3, 'Пт': 4, 'Сб': 5, 'Вс': 6}
selected_days = [day_mapping[d] for d in days_of_week]
df = df[df.index.dayofweek.isin(selected_days)]

# =====================================
# Построение графиков (исправлено)
# =====================================
st.title("🚀 Продвинутый анализатор акций")
fig = go.Figure()

for company in companies:
    col = f'Close_{company}'
    
    # Добавление основного графика
    if chart_type == 'Линия':
        fig.add_trace(go.Scatter(  # ✅ Закрывающая скобка добавлена
            x=df.index,
            y=df[col],
            name=company,
            line=dict(width=2)
        ))  # <-- Здесь была ошибка!
    elif chart_type == 'Свечи' and len(companies) == 1:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df[f'Open_{company}'],
            high=df[f'High_{company}'],
            low=df[f'Low_{company}'],
            close=df[col],
            name=company
        ))
    elif chart_type == 'Область':
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            name=company,
            stackgroup='one',
            mode='lines'
        ))

    # Добавление индикаторов (также проверьте закрывающие скобки!)
    if indicator == 'SMA (20)':
        sma = df[col].rolling(20).mean()
        fig.add_trace(go.Scatter(  # ✅
            x=df.index,
            y=sma,
            name=f'SMA 20 ({company})',
            line=dict(dash='dot')
        ))  # Закрывающая скобка
    elif indicator == 'EMA (50)':
        ema = df[col].ewm(span=50).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ema,
            name=f'EMA 50 ({company})',
            line=dict(dash='dash')
        ))  # Закрывающая скобка
# Добавление горизонтальной линии порога
fig.add_shape(
    type="line",
    x0=df.index.min(),
    x1=df.index.max(),
    y0=price_threshold,
    y1=price_threshold,
    line=dict(color="Red", width=2, dash="dot")
)

# Настройка layout
fig.update_layout(
    height=600,
    showlegend=show_legend,
    hovermode="x unified" if show_hover else False,
    xaxis_rangeslider_visible=False,
    title=f"Динамика цен ({time_resolution.lower()})"
)

st.plotly_chart(fig, use_container_width=True)

# =====================================
# Дополнительные виджеты
# =====================================
# 1. Информационная панель
st.subheader("📊 Статистика за период")

# Динамическое создание колонок (максимум 3)
num_cols = min(len(companies), 3) if companies else 1  # Не менее 1 колонки
cols = st.columns(num_cols)

if companies:
    for idx, company in enumerate(companies):
        # Циклическое распределение по колонкам
        with cols[idx % num_cols]:  
            if f'Close_{company}' in df.columns and not df.empty:
                try:
                    current_price = df[f'Close_{company}'].iloc[-1]
                    delta = current_price - df[f'Close_{company}'].iloc[0]
                    st.metric(
                        label=company,
                        value=f"${current_price:.2f}",
                        delta=f"{delta:.2f} ({delta/df[f'Close_{company}'].iloc[0]*100:.2f}%)"
                    )
                except IndexError:
                    st.error(f"Ошибка данных для {company}")
            else:
                st.error(f"Данные для {company} отсутствуют")
else:
    st.warning("⚠️ Компании не выбраны!")