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

        # 1) 매매방향 색상 스타일링 함수
        def style_direction(val):
            if val == 'BUY':
                return 'color: green; font-weight: bold'
            elif val == 'SELL':
                return 'color: red; font-weight: bold'
            else:
                return ''

        # 2) 실현손익 색상 스타일링 함수
        def style_realized_pnl(val):
            if val > 0:
                return 'color: green; font-weight: bold'
            elif val < 0:
                return 'color: red; font-weight: bold'
            else:
                # 0일 때는 색상 지정 없음
                return ''

        # style 체이닝
        styled_df = (
            display_df.style
            .applymap(style_direction, subset=['매매방향'])
            .applymap(style_realized_pnl, subset=['실현손익'])
        )

        # 데이터프레임 표시
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
from pathlib import Path
import pandas as pd
import streamlit as st

def display_positions():
    try:
        DATA_FILENAME = Path(__file__).parent / 'data/positions.csv'
        
        # 파일이 존재하지 않거나 파일 크기가 0이면 안내 메시지 출력
        if not DATA_FILENAME.exists() or DATA_FILENAME.stat().st_size == 0:
            st.info("현재 오픈 포지션이 없습니다.")
            return
        
        try:
            df = pd.read_csv(DATA_FILENAME)
        except pd.errors.EmptyDataError:
            st.info("현재 오픈 포지션이 없습니다.")
            return

        # DataFrame이 비어있는 경우에도 처리
        if df.empty:
            st.info("현재 오픈 포지션이 없습니다.")
            return

        # 숫자 형식 지정
        format_dict = {
            'Entry Price': '{:.4f}',
            'Break Even Price': '{:.4f}',
            'Current Price': '{:.4f}',
            'Unrealized P&L': '{:.4f}'
        }

        # 매매방향 색상 스타일링 함수
        def style_direction(val):
            if val == 'Long':
                return 'color: green; font-weight: bold'
            elif val == 'Short':
                return 'color: red; font-weight: bold'
            else:
                return ''

        # 미실현 손익 색상 스타일링 함수
        def style_unrealized_pnl(val):
            if val > 0:
                return 'color: green; font-weight: bold'
            elif val < 0:
                return 'color: red; font-weight: bold'
            else:
                return ''

        # 스타일 적용
        styled_df = df.style.format(format_dict)
        styled_df = styled_df.applymap(style_direction, subset=['Side'])
        styled_df = styled_df.applymap(style_unrealized_pnl, subset=['Unrealized P&L'])

        st.subheader("📊 현재 포지션 현황")
        st.dataframe(
            styled_df,
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
st.markdown('''
## :chart_with_upwards_trend: 호롱의 자동매매 대시보드

호롱의 **자동매매 현황**을 확인하세요.

자동매매로 인한 자산 변동 내역이 매일 자정에 자동 업데이트됩니다.

현재 포지션 현황 및 거래 내역은 매 5분마다 자동 업데이트됩니다.

추후 AI 기반 거래 및 예측 등이 업데이트 될 예정입니다.
''')

# -----------------------------------------------------------------------------
# 업데이트 내용 섹션
st.write("---")  # 구분선 추가
st.markdown('''
## :memo: 최근 업데이트 내역

- **2025-02-11:** 실시간 거래 현황에서 동일한 매매건이 수량별로 쪼개져 나오던 문제 수정
''')

# -----------------------------------------------------------------------------
# 메트릭 섹션
st.write("---")  # 구분선 추가

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
base_portfolio = filtered_df.iloc[1]['Start(USDT)']
base_btc = filtered_df.iloc[1]['Market Start(USDT)']

current_portfolio = filtered_df.iloc[-1]['Sum(USDT)']
current_btc = filtered_df.iloc[-1]['Market End(USDT)']

portfolio_return = ((current_portfolio - base_portfolio)/base_portfolio)*100
btc_return = ((current_btc - base_btc)/base_btc)*100
alpha = portfolio_return - btc_return

# 기하평균을 이용한 평균 일수익 계산
daily_returns = filtered_df[1:]['Delta(%)'] / 100  # 백분율을 소수로 변환
geometric_mean_return = (daily_returns + 1).prod() ** (1 / len(daily_returns)) - 1

# 메트릭 레이아웃
col1, col2, col3, col4, col5 = st.columns(5)
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
    st.metric("평균 일수익 ", 
             f"{geometric_mean_return * 100:.2f}%")
with col5:
    last_withdrawl = filtered_df.iloc[-1]['Withdrawl(USDT)']
    st.metric("출금 금액", f"{last_withdrawl:,.0f} USDT")

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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏦 자산 추이", 
    "🆚 vs BTC", 
    "📈 일간 수익(USDT)",   # 새로 추가/이동할 탭
    "📈 일간 수익(%)",     # 기존 tab3였던 (Delta(%)) 차트
    "📋 상세 내역"         # 기존 tab4였던 데이터프레임
])

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

# with tab2:
#     comparison_df = filtered_df.copy()
#     comparison_df['포트폴리오'] = ((comparison_df['End(USDT)'] - base_portfolio)/base_portfolio)*100
#     comparison_df['BTC'] = ((comparison_df['Market End(USDT)'] - base_btc)/base_btc)*100
    
#     portfolio_chart = alt.Chart(comparison_df).mark_line(color='#FF4B4B').encode(
#         x='Datetime:T',
#         y='포트폴리오:Q'
#     )
#     btc_chart = alt.Chart(comparison_df).mark_line(color='#00FF00').encode(
#         x='Datetime:T',
#         y='BTC:Q'
#     )
    
#     combined_chart = (portfolio_chart + btc_chart).resolve_scale(y='shared').properties(height=500)
#     st.altair_chart(combined_chart, use_container_width=True)  # 수정된 부분
    
with tab2:
    # filtered_df: 슬라이더로 선택한 날짜 범위에 따라 필터링 된 데이터프레임
    comparison_df = filtered_df.copy()
    
    # Altair의 transform_calculate를 이용하여, 각각의 컬럼에서 100을 빼는 새 필드를 만듭니다.
    portfolio_chart = alt.Chart(comparison_df).transform_calculate(
        portfolio_adjusted='datum["Percentage(%)"] - 100'
    ).mark_line(color='#FF4B4B').encode(
        x=alt.X('Datetime:T', title='Date'),
        y=alt.Y('portfolio_adjusted:Q', title='포트폴리오 수익률 (%)')
    )
    btc_chart = alt.Chart(comparison_df).transform_calculate(
        btc_adjusted='datum["Market(%)"] - 100'
    ).mark_line(color='#00FF00').encode(
        x=alt.X('Datetime:T', title='Date'),
        y=alt.Y('btc_adjusted:Q', title='BTC 수익률 (%)')
    )
    
    # 두 차트를 하나로 결합하고 동일 y축 스케일 적용
    combined_chart = (portfolio_chart + btc_chart).resolve_scale(y='shared').properties(height=500)
    st.altair_chart(combined_chart, use_container_width=True)

with tab3:
    # 일간 수익(USDT)를 막대그래프로 표시
    chart = alt.Chart(filtered_df[1:]).mark_bar().encode(
        x=alt.X('Date:N', title='Date'),  # 범주형
        y=alt.Y('Delta(USDT):Q', title='Daily P&L (USDT)'),
        color=alt.condition(
            alt.datum['Delta(USDT)'] > 0,
            alt.value('#00FF00'),  # 양수일 때 초록
            alt.value('#FF4B4B')   # 음수일 때 빨강
        )
    ).properties(height=500)
    
    st.altair_chart(chart, use_container_width=True)


with tab4:
    chart = alt.Chart(filtered_df[1:]).mark_bar().encode(
        x=alt.X('Date:N', title='Date'),    # 범주형
        y=alt.Y('Delta(%)', title='Daily Return (%)'),
        color=alt.condition(
            alt.datum['Delta(%)'] > 0,
            alt.value('#00FF00'),  # 양수일 때 초록
            alt.value('#FF4B4B')   # 음수일 때 빨강
        )
    ).properties(height=500)
    
    st.altair_chart(chart, use_container_width=True)


with tab5:
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
    # 분석 대상에서 첫 번째 행(0번)을 제외
    display_df = display_df[1:]

    # 1) 수익(USDT), 수익률(%) 컬럼 스타일링 함수
    def style_profit(val):
        """
        0 이상이면 초록색, 0 미만이면 빨간색으로 표시
        """
        if val >= 0:
            return 'color: green; font-weight: bold;'
        else:
            return 'color: red; font-weight: bold;'

    # 2) Styler 체이닝
    styled_display_df = (
        display_df.style
        # 먼저 스타일 함수 적용(데이터가 숫자일 때 비교)
        .applymap(style_profit, subset=['수익(USDT)', '수익률(%)'])
        # 이후 숫자 서식 적용
        .format({
            '시작 자산': '{:,.0f}',
            '종료 자산': '{:,.0f}',
            '수익(USDT)': '{:,.0f}',
            '수익률(%)': '{:.2f}%',   # 예: 5.00% 로 표시
            'BTC 종가': '{:,.0f}'
        })
    )

    st.dataframe(
        styled_display_df,
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
