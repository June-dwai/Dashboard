import streamlit as st
import pandas as pd
import math
from pathlib import Path
from datetime import datetime
import altair as alt

# 페이지 기본 설정
st.set_page_config(
    page_title='호롱의 대시보드',
    page_icon=':chart_with_upwards_trend:',
    layout='wide'
)

# -----------------------------------------------------------------------------
# 최근 50개 position history 내역
# @st.cache_data(ttl='1h')   # 이거 넣으면 streamlit 자동업데이트가 안 된다. 설마 1시간 마다 업데이트 되나 이러면?
def load_trading_data():
    DATA_FILENAME = Path(__file__).parent/'data/recent_trades.csv'
    df = pd.read_csv(DATA_FILENAME)
    
    # 1. 진입/청산 컬럼 추가
    df['진입/청산'] = df['실현손익'].apply(
        lambda x: '진입' if x == 0 else '청산'
    )
    
    # 2. 수량 컬럼 포함하여 반환
    return df[['심볼', '시간', '매매방향', '가격', '수량', '진입/청산', '실현손익']]

def show_trading_dashboard():
    st.subheader('📈 실시간 거래 현황 (최근 거래내역 50건)')
    
    try:
        display_df = load_trading_data()
        
        # 매매방향 색상 스타일링
        def style_direction(val):
            color = 'green' if val == 'BUY' else 'red'
            return f'color: {color}; font-weight: bold'

        styled_df = display_df.style.applymap(
            style_direction, 
            subset=['매매방향']
        )

        # 데이터프레임 표시 설정
        st.dataframe(
            styled_df,
            column_config={
                "수량": st.column_config.NumberColumn(
                    label="거래 수량",
                    format="%.4f",
                    help="해당 심볼의 거래 수량"
                ),
                "실현손익": st.column_config.NumberColumn(
                    label="실현손익 (USDT)",
                    format="%.4f",
                    help="양수: 수익, 음수: 손실"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=600  # 표 높이 조정
        )
        
    except FileNotFoundError:
        st.error("거래 데이터를 찾을 수 없습니다.")

# -----------------------------------------------------------------------------
# 포지션 로드 함수
def display_positions():
    try:
        DATA_FILENAME = Path(__file__).parent/'data/positions.csv'
        df = pd.read_csv(DATA_FILENAME)
        
        # 숫자 형식 지정
        format_dict = {
            'Entry Price': '{:.4f}',
            'Break Even Price': '{:.4f}',
            'Current Price': '{:.4f}',
            'Unrealized P&L': '{:.4f}'
        }
        
        st.subheader("📊 현재 포지션 현황")
        st.dataframe(
            df.style.format(format_dict),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Symbol": "심볼",
                "Position": st.column_config.NumberColumn("수량", format="%.3f"),
                "Side": "방향",
                "Entry Price": st.column_config.NumberColumn("진입가격", format="%.4f"),
                "Break Even Price": st.column_config.NumberColumn("손익분기점", format="%.4f"),
                "Current Price": st.column_config.NumberColumn("현재가격", format="%.4f"),
                "Unrealized P&L": st.column_config.NumberColumn("미실현손익", format="%.4f")
            }
        )
        
    except FileNotFoundError:
        st.warning("포지션 정보 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"포지션 정보 표시 중 오류 발생: {str(e)}")

# -----------------------------------------------------------------------------
# 데이터 로드 함수
# @st.cache_data(ttl='1h')
def get_trading_data():
    """트레이딩 데이터를 CSV에서 읽어오는 함수"""
    DATA_FILENAME = Path(__file__).parent/'data/daily_report.csv'
    raw_df = pd.read_csv(DATA_FILENAME, parse_dates=['Datetime'])
    
    # 데이터 정제
    df = raw_df.dropna(subset=['End(USDT)'])
    df['Delta(%)'] = df['Delta(%)'].fillna(0)
    
    # 날짜 포맷팅
    df['Date'] = df['Datetime'].dt.strftime('%Y-%m-%d')
    df['Weekday'] = df['Datetime'].dt.day_name()
    
    return df

trading_df = get_trading_data()

# -----------------------------------------------------------------------------
# 페이지 헤더
'''
## :chart_with_upwards_trend: 호롱의 자동매매 대시보드

호롱의 **실시간 자동매매 현황**을 확인하세요.  
알고리즘 기반 거래 내역이 매일 자동 업데이트됩니다.
추후 AI 기반 거래 및 예측 등이 업데이트 될 예정입니다.
'''

# -----------------------------------------------------------------------------
# 메트릭 섹션

# 날짜 범위 선택
dates = trading_df['Datetime'].dt.date.unique()
dates_sorted = sorted(dates)

selected_dates = st.select_slider(
    '📅 기준일 선택',
    options=dates_sorted,
    value=(dates_sorted[0], dates_sorted[-1]),
    format_func=lambda x: x.strftime('%Y-%m-%d')
)
start_date, end_date = selected_dates

# 데이터 필터링
filtered_df = trading_df[
    (trading_df['Datetime'].dt.date >= start_date) & 
    (trading_df['Datetime'].dt.date <= end_date)
]

# 동적 지표 계산
base_portfolio = filtered_df.iloc[0]['End(USDT)']
base_btc = filtered_df.iloc[0]['Market End(USDT)']

current_portfolio = filtered_df.iloc[-1]['End(USDT)']
current_btc = filtered_df.iloc[-1]['Market End(USDT)']

portfolio_return = ((current_portfolio - base_portfolio)/base_portfolio)*100
btc_return = ((current_btc - base_btc)/base_btc)*100
alpha = portfolio_return - btc_return

# 메트릭 레이아웃
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"{start_date} → {end_date} 수익", 
             f"{current_portfolio:,.0f} USDT", 
             f"{portfolio_return:.2f}%")
with col2:
    st.metric("오늘의 BTC 가격 및 수익률", 
             f"{current_btc:,.0f} USDT", 
             f"{btc_return:.2f}%", 
             delta_color="off")
with col3:
    st.metric("알파 수익 (BTC 대비)", 
             f"{alpha:.2f}%", 
             delta_color="normal" if alpha > 0 else "inverse")
with col4:
    st.metric("평균 일수익", 
             f"{filtered_df['Delta(%)'].mean():.2f}%")

st.divider()

# -----------------------------------------------------------------------------
# 차트 섹션

# 날짜 범위 선택 (슬라이더 단일 구현)
dates = trading_df['Datetime'].dt.date.unique()
dates_sorted = sorted(dates)

selected_dates = st.select_slider(
    '📅 분석 기간 선택',
    options=dates_sorted,
    value=(dates_sorted[0], dates_sorted[-1]),
    format_func=lambda x: x.strftime('%Y-%m-%d')
)
start_date, end_date = selected_dates

# 데이터 필터링
filtered_df = trading_df[
    (trading_df['Datetime'].dt.date >= start_date) & 
    (trading_df['Datetime'].dt.date <= end_date)
]

# -----------------------------------------------------------------------------
# 차트 섹션 (탭 구조 변경)

tab1, tab2, tab3, tab4 = st.tabs(["🏦 자산 추이", "🆚 vs BTC", "📈 일간 수익", "📋 상세 내역"])

with tab1:
    # 포트폴리오 추이 (빨강)
    chart = alt.Chart(filtered_df).mark_line(color='#FF4B4B').encode(
        x=alt.X('Datetime:T', title='Date'),
        y=alt.Y('End(USDT):Q', 
                title='USDT',
                scale=alt.Scale(domain=[filtered_df['End(USDT)'].min() * 0.98,
                                       filtered_df['End(USDT)'].max() * 1.02]))
    ).properties(height=500)
    st.altair_chart(chart, use_container_width=True)

with tab2:
    comparison_df = filtered_df.copy()
    comparison_df['포트폴리오'] = ((comparison_df['End(USDT)'] - base_portfolio)/base_portfolio)*100
    comparison_df['BTC'] = ((comparison_df['Market End(USDT)'] - base_btc)/base_btc)*100
    
    portfolio_chart = alt.Chart(comparison_df).mark_line(color='#FF4B4B').encode(
        x='Datetime:T',
        y='포트폴리오:Q'
    )
    btc_chart = alt.Chart(comparison_df).mark_line(color='#00FF00').encode(
        x='Datetime:T',
        y='BTC:Q'
    )
    
    combined_chart = (portfolio_chart + btc_chart).resolve_scale(y='shared').properties(height=500)
    st.altair_chart(combined_chart, use_container_width=True)  # 수정된 부분

with tab3:
    # 일간 수익률 바 차트 (빨강)
    st.bar_chart(
        filtered_df,
        x='Date',
        y='Delta(%)',
        color='#FF4B4B',  # 초록(#00FF00) → 빨강(#FF4B4B)으로 변경
        height=500
    )

with tab4:
    # 데이터프레임 스타일링
    column_mapping = {
        'Date': '거래일',
        'Weekday': '요일',
        'Start(USDT)': '시작 자산',
        'End(USDT)': '종료 자산',
        'Delta(USDT)': '수익(USDT)',
        'Delta(%)': '수익률(%)',
        'Market End(USDT)': 'BTC 종가'
    }
    
    display_df = filtered_df[list(column_mapping.keys())].rename(columns=column_mapping)
    st.dataframe(
        display_df.style.format({
            '시작 자산': '{:,.0f}',
            '종료 자산': '{:,.0f}',
            '수익(USDT)': '{:,.0f}',
            '수익률(%)': '{:.2f}%',
            'BTC 종가': '{:,.0f}'
        }),
        height=500,
        use_container_width=True
    )
  

# -----------------------------------------------------------------------------
# 포지션 히스토리 섹션 (탭 아래 독립된 공간)
st.write("---")  # 구분선 추가
display_positions()  # 함수 호출 위치 변경
  
# -----------------------------------------------------------------------------
# 최근 거래내역 섹션 (탭 아래 독립된 공간)
st.write("---")  # 구분선 추가
show_trading_dashboard()  # 함수 호출 위치 변경
# -----------------------------------------------------------------------------

# 경고문
st.divider()
st.caption('''
⚠️ **투자 경고**  
본 대시보드는 정보 제공 목적으로만 사용됩니다. 실제 거래에 앞서 충분한 연구와 전문가 상담을 권장합니다.  
모든 투자 결정은 투자자 본인의 책임 하에 이루어져야 합니다.
''')
