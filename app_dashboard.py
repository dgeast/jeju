import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="제주 농산품 판매 분석 대시보드", layout="wide")

# 데이터 로드 환경 설정
import glob
import re

# 데이터 로드 환경 설정
def get_latest_data_path():
    # 1. 버전 파일 검색
    files = glob.glob('data/preprocessed_data_*.csv')
    versioned_files = []
    for f in files:
        match = re.search(r'preprocessed_data_(\d+)\.csv', f)
        if match:
             versioned_files.append((f, int(match.group(1))))
    
    if versioned_files:
        # 버전순 정렬 후 최신 파일 반환
        versioned_files.sort(key=lambda x: x[1])
        return versioned_files[-1][0]
    
    # 2. 기본 파일 검색
    if os.path.exists('data/preprocessed_data.csv'):
        return 'data/preprocessed_data.csv'
    return None

DATA_PATH = get_latest_data_path()

@st.cache_data
def load_data(path):
    if path and os.path.exists(path):
        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(path, encoding='cp949')
        
        # 금액 데이터 처리
        def clean_money(val):
            if isinstance(val, str):
                return float(val.replace(',', ''))
            return val
        
        df['실결제 금액'] = df['실결제 금액'].apply(clean_money)
        df['공급단가'] = df['공급단가'].apply(clean_money)
        df['주문-취소 수량'] = pd.to_numeric(df['주문-취소 수량'], errors='coerce').fillna(0)
        df['주문수량'] = pd.to_numeric(df['주문수량'], errors='coerce').fillna(0)
        df['취소수량'] = pd.to_numeric(df['취소수량'], errors='coerce').fillna(0)
        
        # 날짜 처리
        df['주문일'] = pd.to_datetime(df['주문일'])
        df['주문일자'] = df['주문일'].dt.date
        
        # 문자열 컬럼 결측치 및 타입 처리 (정렬 에러 방지)
        df['셀러명'] = df['셀러명'].fillna('미지정').astype(str)
        df['품종'] = df['품종'].fillna('기타').astype(str)
        df['주문경로'] = df['주문경로'].fillna('기타').astype(str)
        df['광역지역(정식)'] = df['광역지역(정식)'].fillna('미정').astype(str)
        
        # 분석용 필드 미리 생성
        df['시간'] = df['주문일'].dt.hour
        df['요일'] = df['주문일'].dt.day_name()
        df['요일번호'] = df['주문일'].dt.weekday # 정렬용
        
        return df
    return None

@st.cache_data
def load_click_data():
    paths = glob.glob('data/salesclick_*.csv')
    if not paths: return None
    
    # 최신 파일 선택
    latest_click_path = sorted(paths)[-1]
    try:
        click_df = pd.read_csv(latest_click_path, encoding='utf-8-sig')
    except:
        click_df = pd.read_csv(latest_click_path, encoding='cp949')
    
    # 합계 컬럼에서 클릭수 추출 (예: "16649 1551 (9.32%)" -> 16649)
    def extract_clicks(val):
        if isinstance(val, str):
            match = re.search(r'^(\d+)', val)
            if match: return int(match.group(1))
        return 0
    
    if '합계' in click_df.columns:
        click_df['클릭수'] = click_df['합계'].apply(extract_clicks)
    else:
        click_df['클릭수'] = 0
        
    return click_df[['상품코드', '클릭수']]

df = load_data(DATA_PATH)

# 캐시/데이터 확인용 메시지 (개발용)
if df is not None:
    if '이벤트 여부' in df.columns:
        st.toast(f"데이터 로드 성공: {os.path.basename(DATA_PATH)} (이벤트 컬럼 포함)")
    else:
        st.toast(f"데이터 로드 성공: {os.path.basename(DATA_PATH)} (이벤트 컬럼 없음!)", icon="⚠️")

if df is not None:
    st.title("🍊 제주 농산품 판매 분석 대시보드")
    
    # 사이드바 필터
    st.sidebar.header("🔍 검색 필터")
    
    # 기간 필터
    min_date = df['주문일자'].min()
    max_date = df['주문일자'].max()
    date_range = st.sidebar.date_input("분석 기간", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    # Top 10 셀러 및 품종 계산 (매출 기준)
    top10_sellers = df.groupby('셀러명')['실결제 금액'].sum().nlargest(10).index.tolist()
    top10_varieties = df.groupby('품종')['실결제 금액'].sum().nlargest(10).index.tolist()
    
    # 필터용 컬럼 생성
    df['셀러명_필터'] = df['셀러명'].apply(lambda x: x if x in top10_sellers else '기타 (Top 10 외)')
    df['품종_필터'] = df['품종'].apply(lambda x: x if x in top10_varieties else '기타 (Top 10 외)')
    
    # 셀러 및 품종 필터 (옵션: Top 10 + 기타)
    seller_options = sorted(top10_sellers) + ['기타 (Top 10 외)']
    variety_options = sorted(top10_varieties) + ['기타 (Top 10 외)']
    
    sellers = st.sidebar.multiselect("셀러 선택 (매출 상위 10 + 기타)", options=seller_options, default=[])
    varieties = st.sidebar.multiselect("품종 선택 (매출 상위 10 + 기타)", options=variety_options, default=[])
    
    # 데이터 필터링 적용
    mask = (df['주문일자'] >= date_range[0]) & (df['주문일자'] <= date_range[1])
    if sellers:
        mask &= df['셀러명_필터'].isin(sellers)
    if varieties:
        mask &= df['품종_필터'].isin(varieties)
    
    filtered_df = df[mask]
    
    # 이익 및 이익률 계산 (전역 적용)
    # 공급단가를 주문수량으로 나눈 단가 사용
    filtered_df['단위공급단가'] = filtered_df['공급단가'] / filtered_df['주문수량']
    filtered_df['단위공급단가'] = filtered_df['단위공급단가'].replace([float('inf'), -float('inf')], 0).fillna(0)
    filtered_df['이익'] = filtered_df['실결제 금액'] - (filtered_df['단위공급단가'] * filtered_df['주문-취소 수량'])
    filtered_df['이익률'] = (filtered_df['이익'] / filtered_df['실결제 금액'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

    # 주요 지표 (KPI)
    # 주요 지표 (KPI)
    st.markdown("### 📌 주요 실적 요약")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_sales = filtered_df['실결제 금액'].sum()
    total_profit = filtered_df['이익'].sum()
    total_qty = filtered_df['주문수량'].sum()
    cancel_qty = filtered_df['취소수량'].sum()
    
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    cancel_rate = (cancel_qty / total_qty * 100) if total_qty > 0 else 0
    avg_order = total_sales / len(filtered_df) if len(filtered_df) > 0 else 0

    with col1:
        st.metric("전체 매출액", f"{total_sales:,.0f}원")
    with col2:
        st.metric("총 주문 건수", f"{len(filtered_df):,}건")
    with col3:
        st.metric("실 판매 수량", f"{filtered_df['주문-취소 수량'].sum():,.0f}개")
    with col4:
        st.metric("평균 객단가", f"{avg_order:,.0f}원")
    with col5:
        st.metric("평균 이익률", f"{avg_margin:.1f}%")
    with col6:
        st.metric("평균 취소율", f"{cancel_rate:.1f}%")

    st.markdown("---")

    # 탭 구성 (채널/심층 통합 반영)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📉 매출 및 성과", 
        "🍏 품종 및 상품", 
        "🔍 셀러 분석(심층/채널)",
        "📉 셀러 활동 및 이탈 분석",
        "🕒 구매패턴(요일/시간별)",
        "👥 고객 분석 및 재구매",
        "📍 핵심 지역 특성 분석",
        "📈 종합 전략 보고서",
    ])

    with tab1:
        st.subheader("📉 매출 추이 및 성과 요약")
        # 일별 집계
        daily_sales = filtered_df.groupby('주문일자').agg({
            '실결제 금액': 'sum',
            '주문번호': 'count'
        }).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=daily_sales['주문일자'], y=daily_sales['실결제 금액'], 
                                       mode='lines+markers', name='매출액', line=dict(color='orange', width=3)))
        fig_trend.update_layout(title="일자별 매출 추이", xaxis_title="날짜", yaxis_title="매출액 (원)")
        st.plotly_chart(fig_trend, use_container_width=True)

        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            # 요일별 누적 매출
            weekday_sum = filtered_df.groupby('요일')['실결제 금액'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).reset_index()
            fig_day_bar = px.bar(weekday_sum, x='요일', y='실결제 금액', title="요일별 누적 매출 실적", color='실결제 금액', color_continuous_scale='Oranges')
            st.plotly_chart(fig_day_bar, use_container_width=True)
        with col_t1b:
            # 가격대별 비중
            price_dist = filtered_df.groupby('가격대')['실결제 금액'].sum().reset_index()
            fig_price_pie = px.pie(price_dist, names='가격대', values='실결제 금액', hole=0.4, title="가격대별 매출 비중")
            st.plotly_chart(fig_price_pie, use_container_width=True)

    with tab2:
        col_t2_1, col_t2_2 = st.columns(2)
        with col_t2_1:
            st.subheader("품종별 매출 비중")
            variety_sales = filtered_df.groupby('품종')['실결제 금액'].sum().reset_index()
            fig_pie_v = px.pie(variety_sales, values='실결제 금액', names='품종', hole=0.4, title="품종별 매출 분포")
            st.plotly_chart(fig_pie_v, use_container_width=True)
        
        with col_t2_2:
            st.subheader("선물세트 상세 분석")
            if '선물세트_여부' in filtered_df.columns:
                gift_df = filtered_df[filtered_df['선물세트_여부'] == '선물세트']
                if not gift_df.empty:
                    gift_pivot = gift_df.groupby(['품종', '과수 크기']).agg({'실결제 금액': 'sum'}).reset_index()
                    fig_sun = px.sunburst(gift_pivot, path=['품종', '과수 크기'], values='실결제 금액', title="선물세트 품종/크기별 분포")
                    st.plotly_chart(fig_sun, use_container_width=True)
                else:
                    st.info("선택된 조건에 선물세트 데이터가 없습니다.")

        st.markdown("---")
        st.subheader("💰 품종별 수익성 분석")
        v_sum = filtered_df.groupby('품종')['실결제 금액'].sum()
        valid_v = v_sum[v_sum > 1000000].index 
        v_stats = filtered_df[filtered_df['품종'].isin(valid_v)].groupby('품종').agg({'이익': 'sum', '실결제 금액': 'sum'})
        v_stats['이익률'] = (v_stats['이익'] / v_stats['실결제 금액'] * 100).fillna(0)
        v_stats = v_stats.sort_values('이익률', ascending=False).reset_index()
        fig_v_margin = px.bar(v_stats, x='품종', y='이익률', color='이익률', title="품종별 평균 판매 이익률 (%)", text_auto='.1f', color_continuous_scale='Greens')
        st.plotly_chart(fig_v_margin, use_container_width=True)

    with tab3:
        st.subheader("🔍 셀러별 상세 심층 지표 및 유입 채널")
        
        # 데이터 집계 (심층 분석용)
        seller_deep = filtered_df.groupby('셀러명').agg({
            '실결제 금액': 'sum', '이익': 'sum', '주문수량': 'sum', '취소수량': 'sum', 'UID': 'nunique', '주문번호': 'count'
        }).rename(columns={'실결제 금액': '매출액', '주문번호': '주문건수', 'UID': '고유고객수'})
        
        seller_deep['이익률(%)'] = (seller_deep['이익'] / seller_deep['매출액'] * 100).round(2)
        seller_deep['재구매율'] = (seller_deep['주문건수'] / seller_deep['고유고객수']).round(2)
        seller_deep = seller_deep.sort_values('매출액', ascending=False)
        
        col_t3_a, col_t3_b = st.columns(2)
        with col_t3_a:
            fig_profit = px.scatter(seller_deep.head(15).reset_index(), x='매출액', y='이익률(%)', size='주문건수', color='이익률(%)', hover_data=['셀러명'], title="TOP 15 셀러: 매출 vs 이익률")
            st.plotly_chart(fig_profit, use_container_width=True)
        with col_t3_b:
            fig_behavior = px.scatter(seller_deep.head(15).reset_index(), x='재구매율', y='매출액', size='주문건수', color='셀러명', title="TOP 15 셀러: 재구매율 vs 매출액")
            st.plotly_chart(fig_behavior, use_container_width=True)

        st.markdown("---")
        st.subheader("� 셀러별 주요 유입 채널 (수익 기여도)")
        if '셀러명' in filtered_df.columns and '주문경로' in filtered_df.columns:
            top_seller_rev = filtered_df.groupby('셀러명')['실결제 금액'].sum().nlargest(10).index
            df_top_seller = filtered_df[filtered_df['셀러명'].isin(top_seller_rev)]
            heatmap_data = pd.crosstab(df_top_seller['셀러명'], df_top_seller['주문경로'], values=df_top_seller['실결제 금액'], aggfunc='sum').fillna(0)
            fig_heat_ch = px.imshow(heatmap_data, text_auto=True, aspect="auto", title="상위 10개 셀러의 채널별 매출 히트맵", color_continuous_scale="Reds")
            st.plotly_chart(fig_heat_ch, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📋 셀러별 상세 분석표")
        st.dataframe(seller_deep.style.format({'매출액': '{:,.0f}', '이익': '{:,.0f}', '이익률(%)': '{:.2f}', '주문건수': '{:,.0f}', '재구매율': '{:.2f}'}), use_container_width=True)

    with tab4:
        st.subheader("📉 셀러 활동성 및 이탈 리스크 분석")
        today = df['주문일자'].max()
        seller_activity = df.groupby('셀러명').agg({'주문일자': 'max', '주문번호': 'count', '실결제 금액': 'sum'}).reset_index()
        seller_activity['일탈일수'] = (today - seller_activity['주문일자']).apply(lambda x: x.days)
        def classify_risk(days):
            if days <= 7: return '🟢 안정 (7일 이내)'
            elif days <= 14: return '🟡 주의 (1~2주)'
            elif days <= 30: return '🟠 위험 (2~4주)'
            else: return '🔴 이탈 의심 (30일 초과)'
        seller_activity['이탈리스크'] = seller_activity['일탈일수'].apply(classify_risk)
        
        c6_1, c6_2 = st.columns([1, 2])
        with c6_1:
            fig_risk = px.pie(seller_activity.groupby('이탈리스크').size().reset_index(name='셀러수'), values='셀러수', names='이탈리스크', title="셀러 이탈 리스크 분포", color='이탈리스크', color_discrete_map={'🟢 안정 (7일 이내)': 'green', '🟡 주의 (1~2주)': 'yellow', '🟠 위험 (2~4주)': 'orange', '🔴 이탈 의심 (30일 초과)': 'red'})
            st.plotly_chart(fig_risk, use_container_width=True)
        with c6_2:
            st.dataframe(seller_activity.sort_values('일탈일수', ascending=False).head(10)[['셀러명', '주문일자', '일탈일수', '이탈리스크']], use_container_width=True)

    with tab5:
        st.subheader("� 요일 및 시간대별 구매패턴 분석")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heat_data = filtered_df.groupby(['요일', '시간'])['실결제 금액'].sum().reset_index()
        heat_pivot = heat_data.pivot(index='요일', columns='시간', values='실결제 금액').reindex(day_order).fillna(0)
        fig_heat_time = px.imshow(heat_pivot, labels=dict(x="시간(Hour)", y="요일(Day)", color="매출액"), x=[f"{h}시" for h in range(24)], y=day_order, color_continuous_scale='Oranges', title="주간 구매 골든타임 히트맵")
        st.plotly_chart(fig_heat_time, use_container_width=True)
        
        peak = heat_data.loc[heat_data['실결제 금액'].idxmax()]
        st.success(f"**💡 핵심 인사이트**: 현재 데이터상 가장 구매가 활발한 요일은 **{peak['요일']}**, 시간대는 **{peak['시간']}시**입니다.")
        
    with tab6:
        st.subheader("👥 고객 분석 및 재구매 패턴")
        cust_stats = filtered_df.groupby('UID').agg({'주문번호': 'count', '실결제 금액': 'sum', '주문일자': ['min', 'max']}).reset_index()
        cust_stats.columns = ['UID', '구매횟수', '총구매액', '최초구매일', '마지막구매일']
        total_cust = len(cust_stats); repeat_cust = len(cust_stats[cust_stats['구매횟수'] > 1])
        st.columns(3)[0].metric("총 고유 고객수", f"{total_cust:,.0f}명"); st.columns(3)[1].metric("재구매 고객수", f"{repeat_cust:,.0f}명"); st.columns(3)[2].metric("재구매율", f"{(repeat_cust/total_cust*100) if total_cust>0 else 0:.1f}%")
        st.plotly_chart(px.bar(cust_stats.groupby('구매횟수').size().reset_index(name='고객수'), x='구매횟수', y='고객수', title="구매 빈도 분포"), use_container_width=True)

        st.markdown("---")
        st.subheader("🎯 셀러별 주문 전환율 (CVR) 분석")
        
        click_df = load_click_data()
        if click_df is not None and df is not None:
            # 셀러-상품코드 매핑 생성
            seller_map = df[['상품코드', '셀러명']].drop_duplicates().groupby('상품코드')['셀러명'].first()
            click_df['셀러명'] = click_df['상품코드'].map(seller_map)
            
            # 셀러별 클릭수 합산
            seller_clicks = click_df.groupby('셀러명')['클릭수'].sum().reset_index()
            
            # 필터링된 셀러별 주문수 합산
            seller_orders = filtered_df.groupby('셀러명').size().reset_index(name='주문건수')
            
            # 병합 및 CVR 계산
            cvr_df = pd.merge(seller_orders, seller_clicks, on='셀러명', how='left').fillna(0)
            cvr_df['CVR'] = (cvr_df['주문건수'] / cvr_df['클릭수'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
            
            # 상위 15개 셀러 시각화
            cvr_plot_df = cvr_df[cvr_df['클릭수'] > 0].sort_values('CVR', ascending=False).head(15)
            
            if not cvr_plot_df.empty:
                fig_cvr = px.bar(cvr_plot_df, x='셀러명', y='CVR', text_auto='.1f', 
                                 title="TOP 15 셀러 주문 전환율 (CVR, %)", 
                                 labels={'CVR': '전환율 (%)', '셀러명': '셀러명'},
                                 color='CVR', color_continuous_scale='Blues')
                st.plotly_chart(fig_cvr, use_container_width=True)
                st.info("💡 **CVR(Conversion Rate)**: 클릭 대비 실제 주문이 발생한 비율입니다. 전환율이 높을수록 마케팅 효율이 좋음을 의미합니다.")
            else:
                st.warning("분석 가능한 클릭 데이터가 없습니다.")
        else:
            st.info("클릭 데이터 파일(salesclick_*.csv)을 찾을 수 없어 전환율 분석을 표시할 수 없습니다.")

    with tab7:
        st.subheader("📍 핵심 지역 특성 분석")
        top_regions = filtered_df.groupby('광역지역(정식)')['실결제 금액'].sum().nlargest(3).index.tolist()
        if top_regions:
            for region in top_regions:
                with st.expander(f"📌 {region} 지역 특성"):
                    r_df = filtered_df[filtered_df['광역지역(정식)'] == region]
                    r_col1, r_col2 = st.columns(2)
                    with r_col1: st.plotly_chart(px.pie(r_df.groupby('품종')['실결제 금액'].sum().reset_index(), values='실결제 금액', names='품종', title=f"{region} 선호 품종"), use_container_width=True)
                    with r_col2: st.plotly_chart(px.bar(r_df.groupby('가격대')['주문번호'].count().reset_index(), x='가격대', y='주문번호', title=f"{region} 선호 가격대"), use_container_width=True)

    with tab8:
        st.subheader("📋 경영 및 마케팅 전략 통합 보고서")
        def load_report(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f: return f.read()
            except: return "보고서 파일을 찾을 수 없습니다."
        r_tab1, r_tab2 = st.tabs(["🚀 마케팅 전략 분석", "📊 EDA 종합 분석"])
        with r_tab1: st.markdown(load_report("docs/analysis/marketing_strategy_report.md"))
        with r_tab2: st.markdown(load_report("docs/analysis/eda_comprehensive_report.md"))

else:
    st.error("데이터 파일을 찾을 수 없습니다. 경로: 'data/preprocessed_data.csv'")
