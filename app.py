import streamlit as st
import pandas as pd
from datetime import time
from numbers import Number

from calculator import calculate_inventory_analysis
from discount_analyzer import analyze_discount_options
from excel_loader import load_excel_file
from route_analyzer import analyze_dc_retailer_routes
from cutline_analyzer import analyze_product_distance_cutline
from time_window_analyzer import analyze_trade_time_windows
from transfer_path_analyzer import analyze_direct_vs_dc_transfer
from promotion_analyzer import analyze_promotion_vs_transfer
from network_path_analyzer import analyze_multi_store_network_paths
from final_summary import build_final_recommendations

from kakao_map_viewer import show_kakao_map, show_kakao_map_with_highlights

try:
    from kakao_map_viewer import show_kakao_map_with_truck
except ImportError:
    show_kakao_map_with_truck = None


# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="Varo",
    page_icon="📦",
    layout="wide"
)


# =========================
# 전역 스타일
# =========================
def apply_global_style():
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #fffdf4 0%, #ffffff 42%, #f8f9fa 100%);
            }

            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #fff8d6 0%, #ffffff 100%);
                border-right: 1px solid #f1e4a8;
            }

            .stButton > button {
                border-radius: 14px;
                border: 1px solid #ffd43b;
                background: linear-gradient(135deg, #fff3bf, #ffd43b);
                color: #222;
                font-weight: 800;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }

            .stButton > button:hover {
                border: 1px solid #fab005;
                background: linear-gradient(135deg, #ffe066, #fcc419);
                color: #111;
            }

            .main-hero {
                padding: 42px 44px;
                border-radius: 32px;
                background:
                    radial-gradient(circle at top left, rgba(255, 212, 59, 0.45), transparent 32%),
                    linear-gradient(135deg, #fff3bf 0%, #fff9db 45%, #ffffff 100%);
                border: 1px solid #f6e58d;
                box-shadow: 0 12px 34px rgba(0,0,0,0.07);
                margin-bottom: 28px;
            }

            .main-hero h1 {
                font-size: 54px;
                margin-bottom: 8px;
                color: #222;
                letter-spacing: -1px;
            }

            .main-hero p {
                font-size: 19px;
                color: #555;
                margin-bottom: 0;
                line-height: 1.65;
            }

            .hero-sub {
                max-width: 860px;
                margin-top: 10px;
            }

            .badge {
                display: inline-block;
                padding: 8px 13px;
                border-radius: 999px;
                background: #fff3bf;
                border: 1px solid #ffd43b;
                font-weight: 700;
                font-size: 13px;
                margin-right: 6px;
                margin-bottom: 6px;
            }

            .blue-badge {
                background: #e7f5ff;
                border: 1px solid #74c0fc;
            }

            .green-badge {
                background: #ebfbee;
                border: 1px solid #8ce99a;
            }

            .pink-badge {
                background: #fff0f6;
                border: 1px solid #faa2c1;
            }

            .mode-card {
                padding: 32px;
                border-radius: 28px;
                border: 1px solid #eee;
                background: #ffffff;
                box-shadow: 0 10px 28px rgba(0,0,0,0.055);
                min-height: 340px;
                transition: 0.2s ease;
                margin-bottom: 12px;
            }

            .mode-card-yellow {
                background:
                    radial-gradient(circle at top right, rgba(255, 212, 59, 0.28), transparent 30%),
                    linear-gradient(135deg, #fffbea 0%, #fff3bf 100%);
                border: 1px solid #ffe066;
            }

            .mode-card-blue {
                background:
                    radial-gradient(circle at top right, rgba(116, 192, 252, 0.25), transparent 30%),
                    linear-gradient(135deg, #eef7ff 0%, #e7f5ff 100%);
                border: 1px solid #a5d8ff;
            }

            .mode-card h3 {
                font-size: 28px;
                margin-bottom: 12px;
            }

            .mode-card p {
                font-size: 15.5px;
                color: #444;
                line-height: 1.7;
            }

            .mode-card ul {
                margin-top: 12px;
                padding-left: 20px;
                color: #555;
                line-height: 1.8;
            }

            .mode-mini {
                margin-top: 16px;
                padding: 12px 14px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.9);
                font-size: 14px;
                color: #444;
            }

            .workflow-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 16px;
                margin-top: 22px;
                margin-bottom: 20px;
            }

            .workflow-card {
                padding: 22px;
                border-radius: 24px;
                background: #ffffff;
                border: 1px solid #eeeeee;
                box-shadow: 0 8px 22px rgba(0,0,0,0.045);
            }

            .workflow-number {
                width: 36px;
                height: 36px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: #ffd43b;
                font-weight: 900;
                margin-bottom: 12px;
            }

            .workflow-title {
                font-size: 18px;
                font-weight: 800;
                margin-bottom: 8px;
            }

            .workflow-text {
                color: #555;
                line-height: 1.6;
                font-size: 14px;
            }

            .mode-header {
                padding: 30px 36px;
                border-radius: 28px;
                background:
                    radial-gradient(circle at top left, rgba(255, 212, 59, 0.30), transparent 30%),
                    linear-gradient(135deg, #fff3bf 0%, #fff9db 55%, #ffffff 100%);
                border: 1px solid #f6e58d;
                box-shadow: 0 10px 26px rgba(0,0,0,0.055);
                margin-top: 18px;
                margin-bottom: 18px;
            }

            .mode-header h2 {
                font-size: 34px;
                margin-bottom: 8px;
                letter-spacing: -0.5px;
            }

            .mode-header p {
                font-size: 16px;
                color: #555;
                margin-bottom: 0;
                line-height: 1.65;
            }

            .feature-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 14px;
                margin-top: 16px;
                margin-bottom: 18px;
            }

            .feature-card {
                padding: 18px;
                border-radius: 20px;
                background: #ffffff;
                border: 1px solid #eeeeee;
                box-shadow: 0 6px 18px rgba(0,0,0,0.04);
            }

            .feature-icon {
                font-size: 25px;
                margin-bottom: 6px;
            }

            .feature-title {
                font-weight: 800;
                margin-bottom: 6px;
            }

            .feature-desc {
                color: #666;
                font-size: 13.5px;
                line-height: 1.55;
            }

            .section-card {
                padding: 24px 28px;
                border-radius: 22px;
                border: 1px solid #eeeeee;
                background: #ffffff;
                box-shadow: 0 6px 18px rgba(0,0,0,0.04);
                margin-top: 18px;
                margin-bottom: 18px;
            }

            .best-card {
                padding: 26px 30px;
                border-radius: 26px;
                background:
                    radial-gradient(circle at top right, rgba(255, 212, 59, 0.34), transparent 32%),
                    linear-gradient(135deg, #fffbea 0%, #fff3bf 48%, #ffffff 100%);
                border: 2px solid #ffd43b;
                box-shadow: 0 10px 28px rgba(0,0,0,0.07);
                margin-top: 16px;
                margin-bottom: 22px;
            }

            .best-title {
                font-size: 25px;
                font-weight: 900;
                margin-bottom: 14px;
                color: #222;
            }

            .best-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 14px;
                margin-top: 12px;
                margin-bottom: 16px;
            }

            .best-mini {
                padding: 14px;
                border-radius: 18px;
                background: rgba(255,255,255,0.78);
                border: 1px solid rgba(255,255,255,0.9);
            }

            .best-label {
                color: #666;
                font-size: 13px;
                margin-bottom: 5px;
            }

            .best-value {
                font-size: 18px;
                font-weight: 900;
                color: #222;
            }

            .best-reason {
                padding: 16px 18px;
                border-radius: 18px;
                background: rgba(255,255,255,0.84);
                border: 1px solid rgba(255,255,255,0.95);
                line-height: 1.7;
                color: #444;
            }

            .mini-guide {
                padding: 18px 20px;
                border-radius: 20px;
                background: #ffffff;
                border: 1px solid #eeeeee;
                color: #444;
                line-height: 1.7;
                margin-top: 14px;
                margin-bottom: 18px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.035);
            }

            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #eeeeee;
                padding: 16px;
                border-radius: 18px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.035);
            }

            .footer-note {
                text-align: center;
                color: #777;
                font-size: 13px;
                padding-top: 18px;
            }

            @media (max-width: 900px) {
                .workflow-grid {
                    grid-template-columns: 1fr;
                }

                .feature-grid {
                    grid-template-columns: 1fr 1fr;
                }

                .best-grid {
                    grid-template-columns: 1fr 1fr;
                }

                .main-hero h1 {
                    font-size: 40px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True
    )


apply_global_style()


# =========================
# 상태 초기화
# =========================
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None

if "cart" not in st.session_state:
    st.session_state.cart = []


# =========================
# 공통 UI
# =========================
def format_money(value):
    if isinstance(value, Number):
        return f"{value:,.0f}원"

    try:
        numeric_value = float(value)
        return f"{numeric_value:,.0f}원"
    except Exception:
        return str(value)


def get_best_recommendation(final_recommendations):
    if final_recommendations.empty:
        return None

    temp = final_recommendations.copy()
    temp["_cost_numeric"] = pd.to_numeric(temp["estimated_cost"], errors="coerce")

    if temp["_cost_numeric"].notna().any():
        temp = temp.sort_values("_cost_numeric", ascending=True)
        return temp.iloc[0]

    return temp.iloc[0]


def render_best_recommendation(final_recommendations):
    best_row = get_best_recommendation(final_recommendations)

    if best_row is None:
        return

    product_name = best_row.get("product_name", "-")
    source_store = best_row.get("source_store", "-")
    target_store = best_row.get("target_store", "-")
    suggested_qty = best_row.get("suggested_qty", "-")
    final_recommendation = best_row.get("final_recommendation", "-")
    estimated_cost = best_row.get("estimated_cost", "-")
    reason = best_row.get("reason", "-")

    html = (
        '<div class="best-card">'
        '<div class="best-title">✅ 최적 추천 대표 경로</div>'

        '<div class="best-grid">'

        '<div class="best-mini">'
        '<div class="best-label">상품명</div>'
        f'<div class="best-value">{product_name}</div>'
        '</div>'

        '<div class="best-mini">'
        '<div class="best-label">추천 경로</div>'
        f'<div class="best-value">{source_store} → {target_store}</div>'
        '</div>'

        '<div class="best-mini">'
        '<div class="best-label">추천 수량</div>'
        f'<div class="best-value">{suggested_qty}개</div>'
        '</div>'

        '<div class="best-mini">'
        '<div class="best-label">예상 비용</div>'
        f'<div class="best-value">{format_money(estimated_cost)}</div>'
        '</div>'

        '</div>'

        '<div class="best-reason">'
        f'<b>추천 전략:</b> {final_recommendation}<br>'
        f'<b>추천 이유:</b> {reason}<br>'
        '<b>설명:</b> 이 대표 경로는 최종 추천 목록 중 예상 비용이 가장 낮은 경로를 기준으로 표시됩니다.'
        '</div>'

        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def show_main_hero():
    st.markdown(
        """
        <div class="main-hero">
            <h1>📦 Varo</h1>
            <p class="hero-sub">
                편의점 악성재고를 줄이기 위해 재고 상태, 이동 비용, 프로모션 효과, 최적 경로를 함께 분석하는
                <b>재고 공유 및 의사결정 지원 시스템</b>입니다.
            </p>
            <div style="margin-top:20px;">
                <span class="badge">악성재고 판단</span>
                <span class="badge">최적 재배치</span>
                <span class="badge blue-badge">카카오맵 시각화</span>
                <span class="badge green-badge">Inventory 변화</span>
                <span class="badge pink-badge">Truck 시뮬레이션</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_workflow():
    st.markdown(
        """
        <div class="workflow-grid">
            <div class="workflow-card">
                <div class="workflow-number">1</div>
                <div class="workflow-title">데이터 입력</div>
                <div class="workflow-text">
                    단일 상품을 직접 입력하거나, 여러 점포의 재고·상품·경로 데이터를 엑셀로 업로드합니다.
                </div>
            </div>
            <div class="workflow-card">
                <div class="workflow-number">2</div>
                <div class="workflow-title">의사결정 분석</div>
                <div class="workflow-text">
                    유지, 할인, 폐기, 점포 이동, DC 경유, 다중 경로를 비교해 최적 처리 방식을 추천합니다.
                </div>
            </div>
            <div class="workflow-card">
                <div class="workflow-number">3</div>
                <div class="workflow-title">지도·재고 시각화</div>
                <div class="workflow-text">
                    추천 경로를 지도에 표시하고, Truck 이동 후 점포별 Inventory 변화를 대시보드로 확인합니다.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_mode_header(title, description, badges=None):
    badge_html = ""

    if badges:
        for badge in badges:
            badge_html += f'<span class="badge">{badge}</span>'

    st.markdown(
        f"""
        <div class="mode-header">
            <h2>{title}</h2>
            <p>{description}</p>
            <div style="margin-top:14px;">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_back_button():
    if st.button("← 방식 선택 화면으로 돌아가기"):
        st.session_state.selected_mode = None
        st.rerun()


def show_excel_feature_cards():
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🧭</div>
                <div class="feature-title">최적 경로 추천</div>
                <div class="feature-desc">직접 이동, DC 경유, 다중 경로를 비교해 더 효율적인 이동 방식을 찾습니다.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🚚</div>
                <div class="feature-title">Truck 시뮬레이션</div>
                <div class="feature-desc">추천 경로를 따라 Truck이 이동하는 모습을 카카오맵 위에서 확인합니다.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📦</div>
                <div class="feature-title">Inventory 변화</div>
                <div class="feature-desc">보내는 점포와 받는 점포의 이동 전후 재고 변화를 카드와 그래프로 보여줍니다.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎁</div>
                <div class="feature-title">프로모션 비교</div>
                <div class="feature-desc">재배치 비용과 할인/1+1 프로모션 비용을 비교해 처리 전략을 추천합니다.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 첫 화면
# =========================
def show_mode_selector():
    show_main_hero()

    st.markdown("### 사용할 방식을 선택하세요")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="mode-card mode-card-yellow">
                <h3>🧮 개별 입력 계산</h3>
                <p>
                점포명, 상품명, 재고 수량, 판매량, 할인율, 이동 가능 여부를 직접 입력해서
                악성재고 여부와 처리 전략을 빠르게 계산합니다.
                </p>
                <p><b>추천 상황</b></p>
                <ul>
                    <li>단일 상품을 빠르게 테스트할 때</li>
                    <li>계산 원리를 설명할 때</li>
                    <li>발표에서 기본 구조를 시연할 때</li>
                </ul>
                <div class="mode-mini">
                    입력값을 바꾸면 비용 비교와 추천 전략이 어떻게 달라지는지 확인할 수 있습니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🧮 개별 입력 계산 시작", use_container_width=True, type="primary"):
            st.session_state.selected_mode = "single"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="mode-card mode-card-blue">
                <h3>📊 엑셀 기반 최적 경로 추천</h3>
                <p>
                여러 점포, 상품, 재고, 경로 데이터를 엑셀로 업로드하여
                최적 재배치 경로와 처리 전략을 종합 분석합니다.
                </p>
                <p><b>추천 상황</b></p>
                <ul>
                    <li>여러 점포를 동시에 분석할 때</li>
                    <li>최적 이동 경로를 추천받고 싶을 때</li>
                    <li>지도와 Truck 이동을 시각화할 때</li>
                </ul>
                <div class="mode-mini">
                    최종 추천, 지도 시각화, Inventory 변화 대시보드까지 한 번에 확인합니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("📊 엑셀 기반 분석 시작", use_container_width=True, type="primary"):
            st.session_state.selected_mode = "excel"
            st.rerun()

    show_workflow()

    st.markdown(
        """
        <div class="mini-guide">
            <b>추천 사용 순서</b><br>
            처음에는 <b>개별 입력 계산</b>으로 악성재고 판단 원리를 확인하고,
            이후 <b>엑셀 기반 최적 경로 추천</b>으로 여러 점포 분석과 Truck 시뮬레이션을 확인하는 흐름을 추천합니다.
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 1. 개별 입력 계산 모드
# =========================
def show_single_calculator():
    show_back_button()

    show_mode_header(
        "🧮 개별 입력 기반 악성재고 계산",
        "단일 점포와 단일 상품을 기준으로 악성재고 여부, 비용 비교, 최종 처리 전략을 계산합니다.",
        ["단일 상품", "직접 입력", "비용 비교", "계산식 확인"]
    )

    st.sidebar.header("개별 입력값 설정")

    store_name = st.sidebar.text_input("점포명", "강남점")
    product_name = st.sidebar.text_input("상품명", "삼각김밥")

    stock_qty = st.sidebar.number_input("현재 재고 수량", min_value=0, value=100)
    sales_30d = st.sidebar.number_input("최근 30일 판매량", min_value=0, value=5)
    inbound_days = st.sidebar.number_input("입고 후 지난 일수", min_value=0, value=50)

    unit_cost = st.sidebar.number_input("상품 1개당 원가(원)", min_value=0, value=1500)
    daily_holding_cost = st.sidebar.number_input("하루 보관비(원)", min_value=0, value=20)
    disposal_cost_per_unit = st.sidebar.number_input("상품 1개당 폐기비용(원)", min_value=0, value=300)

    discount_rate = st.sidebar.number_input(
        "할인율(%)",
        min_value=0.0,
        max_value=100.0,
        value=20.0
    )

    expected_sales_increase_rate = st.sidebar.number_input(
        "할인 시 판매 증가율(%)",
        min_value=0.0,
        value=50.0
    )

    transfer_possible = st.sidebar.selectbox("타점포 이동 가능 여부", ["가능", "불가능"])
    distance_km = st.sidebar.number_input("점포 간 거리(km)", min_value=0.0, value=10.0)
    cost_per_km = st.sidebar.number_input("km당 운송비(원)", min_value=0.0, value=500.0)
    target_store_sales_30d = st.sidebar.number_input("이동 대상 점포 최근 30일 판매량", min_value=0, value=20)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("입력 정보")

    col_a, col_b = st.columns(2)
    col_a.write(f"점포명: **{store_name}**")
    col_b.write(f"상품명: **{product_name}**")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("계산 시작", type="primary", use_container_width=True):
        result = calculate_inventory_analysis(
            stock_qty=stock_qty,
            sales_30d=sales_30d,
            inbound_days=inbound_days,
            unit_cost=unit_cost,
            daily_holding_cost=daily_holding_cost,
            discount_rate=discount_rate,
            expected_sales_increase_rate=expected_sales_increase_rate,
            transfer_possible=(transfer_possible == "가능"),
            distance_km=distance_km,
            cost_per_km=cost_per_km,
            target_store_sales_30d=target_store_sales_30d,
            disposal_cost_per_unit=disposal_cost_per_unit,
        )

        discount_comparison = analyze_discount_options(
            stock_qty=stock_qty,
            sales_30d=sales_30d,
            unit_cost=unit_cost,
            daily_holding_cost=daily_holding_cost,
            discount_rates=[10, 20, 30, 40],
            expected_sales_increase_rate=expected_sales_increase_rate,
        )

        st.success("계산이 완료되었습니다.")

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("악성재고 판단 결과")

        col1, col2, col3 = st.columns(3)

        col1.metric("재고소진 예상일수", f"{result['stock_cover_days']}일")
        col2.metric("위험점수", f"{result['risk_score']}점")
        col3.metric("악성재고 여부", "예" if result["is_bad_stock"] else "아니오")

        st.subheader("판단 이유")

        if result["reasons"]:
            for reason in result["reasons"]:
                st.write(f"- {reason}")
        else:
            st.write("위험 요소가 크지 않습니다.")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("비용 비교")

        if result["transfer_net_cost"] is not None:
            cost_df = pd.DataFrame(
                {
                    "전략": ["유지", "할인", "타점포 이동", "폐기"],
                    "비용": [
                        result["keep_cost"],
                        result["discount_net_cost"],
                        result["transfer_net_cost"],
                        result["disposal_cost"],
                    ],
                }
            )
        else:
            cost_df = pd.DataFrame(
                {
                    "전략": ["유지", "할인", "폐기"],
                    "비용": [
                        result["keep_cost"],
                        result["discount_net_cost"],
                        result["disposal_cost"],
                    ],
                }
            )

        st.dataframe(cost_df, use_container_width=True)
        st.bar_chart(cost_df, x="전략", y="비용")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("최종 추천")

        st.success(f"추천 전략: {result['best_action']}")
        st.write(f"추천 이유: {result['recommendation_reason']}")
        st.write(f"발주 조언: **{result['order_advice']}**")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("할인율별 비교")

        st.dataframe(discount_comparison)

        discount_chart_data = pd.DataFrame(
            {
                "할인율": [f"{item['discount_rate']}%" for item in discount_comparison],
                "순비용": [item["net_cost"] for item in discount_comparison],
            }
        )

        st.bar_chart(discount_chart_data, x="할인율", y="순비용")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("계산 방식 보기"):
            st.write(result["formula_text"]["stock_cover_days_formula"])
            st.write(result["formula_text"]["risk_formula"])
            st.write(result["formula_text"]["keep_cost_formula"])
            st.write(result["formula_text"]["discount_formula"])
            st.write(result["formula_text"]["transfer_formula"])
            st.write(result["formula_text"]["disposal_formula"])


# =========================
# 2. 엑셀 기반 최적 경로 추천 모드
# =========================
def show_excel_optimizer():
    show_back_button()

    show_mode_header(
        "📊 엑셀 기반 최적 경로 추천",
        "여러 점포, 상품, 재고, 경로 데이터를 기반으로 최적 재배치와 Truck 이동을 분석합니다.",
        ["엑셀 업로드", "최적 경로", "카카오맵", "Truck 시뮬레이션", "Inventory 변화"]
    )

    show_excel_feature_cards()

    st.sidebar.header("지도 설정")

    kakao_js_key = st.sidebar.text_input(
        "카카오맵 JavaScript 키 입력",
        type="password",
        help="카카오 개발자 사이트에서 복사한 JavaScript 키를 입력하세요."
    )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("엑셀 파일 입력")

    uploaded_file = st.file_uploader(
        "편의점 재고 데이터 엑셀 파일을 업로드하세요",
        type=["xlsx"]
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is None:
        st.info("엑셀 파일을 업로드하면 분석이 시작됩니다.")
        return

    excel_data, missing_sheets = load_excel_file(uploaded_file)

    if missing_sheets:
        st.error(f"엑셀 파일에 필요한 시트가 없습니다: {missing_sheets}")
        return

    st.success("엑셀 파일을 성공적으로 불러왔습니다.")

    stores = excel_data["stores"]
    products = excel_data["products"]
    inventory = excel_data["inventory"]
    routes = excel_data["routes"]

    # =========================
    # 데이터 요약
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("데이터 요약")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("점포/DC 수", f"{len(stores)}개")
    col2.metric("상품 수", f"{len(products)}개")
    col3.metric("재고 데이터", f"{len(inventory)}건")
    col4.metric("경로 데이터", f"{len(routes)}건")

    with st.expander("원본 엑셀 데이터 보기"):
        st.write("stores 시트")
        st.dataframe(stores)

        st.write("products 시트")
        st.dataframe(products)

        st.write("inventory 시트")
        st.dataframe(inventory)

        st.write("routes 시트")
        st.dataframe(routes)

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 분석 조건
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("분석 조건 설정")

    setting_col1, setting_col2, setting_col3 = st.columns(3)

    with setting_col1:
        departure_time = st.time_input(
            "DC/점포 출발 예정 시간",
            value=time(9, 0),
            key="departure_time_excel"
        )

    with setting_col2:
        promotion_type = st.selectbox(
            "프로모션 유형",
            ["할인 프로모션", "1+1 프로모션"],
            key="promotion_type_excel"
        )

    with setting_col3:
        promotion_discount_rate = st.number_input(
            "프로모션 할인율(%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            key="promotion_discount_rate_excel"
        )

    setting_col4, setting_col5 = st.columns(2)

    with setting_col4:
        promotion_sales_increase_rate = st.number_input(
            "프로모션 예상 판매 증가율(%)",
            min_value=0.0,
            max_value=500.0,
            value=80.0,
            key="promotion_sales_increase_rate_excel"
        )

    with setting_col5:
        promotion_fixed_cost = st.number_input(
            "프로모션 고정비(원)",
            min_value=0,
            value=0,
            key="promotion_fixed_cost_excel"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 분석 계산
    # =========================
    dc_routes, best_dc_by_retailer = analyze_dc_retailer_routes(stores, routes)

    if dc_routes.empty:
        cutline_result = None
        best_valid_routes = None
        no_valid_items = None
        time_result = None
        time_error = "DC와 점포를 연결하는 route 데이터가 없어 컷라인/시간 분석을 할 수 없습니다."
    else:
        cutline_result, best_valid_routes, no_valid_items = analyze_product_distance_cutline(
            products,
            inventory,
            dc_routes
        )

        time_result, time_error = analyze_trade_time_windows(
            cutline_result,
            stores,
            departure_time
        )

    transfer_path_result = analyze_direct_vs_dc_transfer(
        stores,
        products,
        inventory,
        routes,
        departure_time
    )

    promotion_result = analyze_promotion_vs_transfer(
        stores,
        inventory,
        transfer_path_result,
        promotion_type,
        promotion_discount_rate,
        promotion_sales_increase_rate,
        promotion_fixed_cost
    )

    network_path_result, network_error = analyze_multi_store_network_paths(
        stores,
        products,
        routes,
        transfer_path_result,
        departure_time
    )

    final_recommendations, final_rec_summary = build_final_recommendations(
        promotion_result,
        network_path_result
    )

    # =========================
    # 최종 추천
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("최종 추천 모아보기")

    if final_recommendations.empty:
        st.info("최종 추천으로 정리할 결과가 없습니다.")
    else:
        render_best_recommendation(final_recommendations)

        summary_col1, summary_col2 = st.columns(2)

        summary_col1.metric("최종 추천 건수", f"{len(final_recommendations)}건")
        summary_col2.metric("추천 유형 수", f"{len(final_rec_summary)}개")

        st.write("추천 유형 요약")
        st.dataframe(final_rec_summary)

        st.bar_chart(
            final_rec_summary.set_index("final_recommendation")["count"]
        )

        st.write("최종 추천 상세")
        st.dataframe(
            final_recommendations[
                [
                    "product_name",
                    "source_store",
                    "target_store",
                    "suggested_qty",
                    "final_recommendation",
                    "estimated_cost",
                    "reason",
                ]
            ]
        )

        st.subheader("🧺 Inventory 장바구니 담기")

        final_recommendations_view = final_recommendations.reset_index(drop=True)

        selected_index = st.selectbox(
            "장바구니에 담을 추천 항목 선택",
            final_recommendations_view.index,
            format_func=lambda i: (
                f"{final_recommendations_view.loc[i, 'product_name']} | "
                f"{final_recommendations_view.loc[i, 'source_store']} → "
                f"{final_recommendations_view.loc[i, 'target_store']} | "
                f"{final_recommendations_view.loc[i, 'final_recommendation']}"
            ),
            key="cart_select_recommendation"
        )

        if st.button("🛒 Inventory에 담기", key="add_to_inventory_cart"):
            selected_row = final_recommendations_view.loc[selected_index]

            cart_item = {
                "상품명": selected_row["product_name"],
                "보내는 점포": selected_row["source_store"],
                "받는 점포": selected_row["target_store"],
                "수량": selected_row["suggested_qty"],
                "추천 전략": selected_row["final_recommendation"],
                "예상 비용": selected_row["estimated_cost"],
                "추천 이유": selected_row["reason"],
            }

            st.session_state.cart.append(cart_item)
            st.success("Inventory 장바구니에 담았습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # Inventory 장바구니
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🧾 Inventory 장바구니")

    if len(st.session_state.cart) == 0:
        st.info("장바구니가 비어있습니다.")
    else:
        for i, item in enumerate(st.session_state.cart):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])

            with c1:
                st.write(
                    f"**{item['상품명']}** / "
                    f"{item['보내는 점포']} → {item['받는 점포']}"
                )
                st.caption(f"추천 이유: {item['추천 이유']}")

            with c2:
                st.write(f"수량: {item['수량']}개")

            with c3:
                st.write(f"전략: {item['추천 전략']}")

                cost_value = item["예상 비용"]
                if isinstance(cost_value, Number):
                    st.write(f"예상 비용: {cost_value:,.0f}원")
                else:
                    st.write(f"예상 비용: {cost_value}")

            with c4:
                if st.button("삭제", key=f"delete_cart_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()

        total_cost = sum(
            item["예상 비용"]
            for item in st.session_state.cart
            if isinstance(item["예상 비용"], Number)
        )

        cart_col1, cart_col2 = st.columns(2)

        cart_col1.metric("담긴 추천 항목 수", f"{len(st.session_state.cart)}건")
        cart_col2.metric("총 예상 비용", f"{total_cost:,.0f}원")

        if st.button("장바구니 전체 비우기", key="clear_inventory_cart"):
            st.session_state.cart = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 카카오맵
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("카카오맵 기반 점포 및 경로 시각화")

    if kakao_js_key:
        show_kakao_map(stores, routes, kakao_js_key)
    else:
        st.info("카카오맵을 보려면 왼쪽 사이드바에 JavaScript 키를 입력하세요.")

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 추천 경로 강조
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("추천 경로 강조 지도")

    highlight_paths = []

    if not transfer_path_result.empty:
        recommended_transfer_paths = transfer_path_result[
            transfer_path_result["recommended_path"] != "이동 비추천"
        ]

        for _, path_row in recommended_transfer_paths.iterrows():
            if path_row["recommended_path"] == "직접 이동 추천":
                path_names = [
                    path_row["source_store"],
                    path_row["target_store"],
                ]

            elif path_row["recommended_path"] == "DC 경유 이동 추천":
                path_names = [
                    path_row["source_store"],
                    path_row["via_dc"],
                    path_row["target_store"],
                ]

            else:
                continue

            highlight_paths.append(
                {
                    "path_names": path_names,
                    "label": f"{path_row['product_name']} - {path_row['recommended_path']}",
                }
            )

    if not network_path_result.empty:
        network_recommended_paths = network_path_result[
            network_path_result["network_recommendation"] == "다중 경로 추천"
        ]

        for _, network_row in network_recommended_paths.iterrows():
            path_names = str(network_row["network_path"]).split(" → ")

            highlight_paths.append(
                {
                    "path_names": path_names,
                    "label": f"{network_row['product_name']} - 다중 경로 추천",
                }
            )

    if kakao_js_key and highlight_paths:
        show_kakao_map_with_highlights(
            stores,
            routes,
            kakao_js_key,
            highlight_paths
        )
    elif not kakao_js_key:
        st.info("추천 경로 지도를 보려면 왼쪽 사이드바에 카카오맵 JavaScript 키를 입력하세요.")
    else:
        st.info("강조 표시할 추천 경로가 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # Truck 이동 + Inventory 변화
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🚚 Truck 이동 시뮬레이션 + Inventory 변화")

    truck_speed = st.slider(
        "Truck 이동 배속",
        min_value=0.5,
        max_value=10.0,
        value=1.0,
        step=0.5,
        key="truck_speed_slider"
    )

    store_location_map = {}

    for _, row in stores.iterrows():
        if (
            pd.notna(row.get("store_name"))
            and pd.notna(row.get("latitude"))
            and pd.notna(row.get("longitude"))
        ):
            store_location_map[row["store_name"]] = {
                "name": row["store_name"],
                "lat": float(row["latitude"]),
                "lng": float(row["longitude"]),
            }

    truck_path = []
    inventory_change_info = {}

    if highlight_paths:
        first_path_names = highlight_paths[0]["path_names"]

        for store_name_in_path in first_path_names:
            if store_name_in_path in store_location_map:
                truck_path.append(store_location_map[store_name_in_path])

    if not transfer_path_result.empty:
        transfer_candidates = transfer_path_result[
            transfer_path_result["recommended_path"] != "이동 비추천"
        ].copy()
    else:
        transfer_candidates = pd.DataFrame()

    if not transfer_candidates.empty:
        selected_transfer = transfer_candidates.iloc[0]

        selected_product_name = selected_transfer["product_name"]
        source_store_name = selected_transfer["source_store"]
        target_store_name = selected_transfer["target_store"]

        try:
            move_qty = int(selected_transfer["suggested_transfer_qty"])
        except Exception:
            move_qty = 0

        store_name_to_id = dict(zip(stores["store_name"], stores["store_id"]))
        product_name_to_id = dict(zip(products["product_name"], products["product_id"]))

        source_store_id = store_name_to_id.get(source_store_name)
        target_store_id = store_name_to_id.get(target_store_name)
        product_id = product_name_to_id.get(selected_product_name)

        def get_current_stock(store_id, product_id_value):
            if store_id is None or product_id_value is None:
                return 0

            matched = inventory[
                (inventory["store_id"] == store_id)
                & (inventory["product_id"] == product_id_value)
            ]

            if matched.empty:
                return 0

            return int(matched.iloc[0]["stock_qty"])

        source_before = get_current_stock(source_store_id, product_id)
        target_before = get_current_stock(target_store_id, product_id)

        source_after = max(source_before - move_qty, 0)
        target_after = target_before + move_qty

        store_inventory = {
            source_store_name: {
                "role": "보내는 점포",
                "product_name": selected_product_name,
                "before": source_before,
                "after": source_after,
                "change": -move_qty,
            },
            target_store_name: {
                "role": "받는 점포",
                "product_name": selected_product_name,
                "before": target_before,
                "after": target_after,
                "change": move_qty,
            },
        }

        if selected_transfer["recommended_path"] == "DC 경유 이동 추천":
            via_dc_name = selected_transfer.get("via_dc", None)

            if via_dc_name:
                via_dc_id = store_name_to_id.get(via_dc_name)
                via_before = get_current_stock(via_dc_id, product_id)

                store_inventory[via_dc_name] = {
                    "role": "경유 DC",
                    "product_name": selected_product_name,
                    "before": via_before,
                    "after": via_before,
                    "change": 0,
                }

        inventory_change_info = {
            "product_name": selected_product_name,
            "move_qty": move_qty,
            "source_store": source_store_name,
            "target_store": target_store_name,
            "recommended_path": selected_transfer["recommended_path"],
            "store_inventory": store_inventory,
        }

    if show_kakao_map_with_truck is None:
        st.warning("kakao_map_viewer.py에 show_kakao_map_with_truck 함수가 없습니다.")

    elif kakao_js_key and len(truck_path) >= 2:
        st.info("최적 추천 경로를 기준으로 Truck 이동과 Inventory 변화를 시뮬레이션합니다.")

        show_kakao_map_with_truck(
            stores,
            routes,
            kakao_js_key,
            truck_path,
            speed_multiplier=truck_speed,
            inventory_changes=inventory_change_info,
        )

    elif not kakao_js_key:
        st.info("Truck 이동 시뮬레이션을 보려면 왼쪽 사이드바에 카카오맵 JavaScript 키를 입력하세요.")
    else:
        st.info("Truck 이동을 표시할 추천 경로가 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 상세 분석 결과
    # =========================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("상세 분석 결과")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "DC-점포",
            "거리 컷라인",
            "거래가능시간",
            "직접 vs DC 경유",
            "프로모션 비교",
            "다중 경로",
        ]
    )

    with tab1:
        st.subheader("DC-점포 거리 및 운송비 계산")

        if dc_routes.empty:
            st.warning("DC와 점포를 연결하는 route 데이터가 없습니다.")
        else:
            st.write("DC-점포 전체 경로 계산 결과")
            st.dataframe(dc_routes)

            st.write("점포별 최적 DC 추천")
            st.dataframe(best_dc_by_retailer)

            st.write("점포별 최저 운송비 그래프")
            chart_data = best_dc_by_retailer.set_index("retailer_name")["transport_cost"]
            st.bar_chart(chart_data)

    with tab2:
        st.subheader("제품별 거리 컷라인 판별")

        if cutline_result is None or cutline_result.empty:
            st.warning("제품별 거리 컷라인 분석 결과가 없습니다.")
        else:
            st.write("제품별 DC-점포 이동 가능 여부")
            st.dataframe(cutline_result)

            st.write("제품별/점포별 컷라인 내 최적 DC")
            if best_valid_routes.empty:
                st.warning("거리 컷라인을 만족하는 이동 가능 경로가 없습니다.")
            else:
                st.dataframe(best_valid_routes)

            st.write("거리 컷라인 때문에 이동 불가능한 품목")
            if no_valid_items.empty:
                st.success("모든 품목이 최소 1개 이상의 이동 가능 경로를 가지고 있습니다.")
            else:
                st.dataframe(no_valid_items)

    with tab3:
        st.subheader("거래가능시간 판별")

        if time_error:
            st.warning(time_error)
        elif time_result is None or time_result.empty:
            st.warning("거래가능시간 분석 결과가 없습니다.")
        else:
            st.write("거리 컷라인 + 거래가능시간 판별 결과")
            st.dataframe(time_result)

            time_summary = (
                time_result.groupby("final_status")
                .size()
                .reset_index(name="count")
            )

            st.write("최종 이동 가능 여부 요약")
            st.dataframe(time_summary)
            st.bar_chart(time_summary.set_index("final_status")["count"])

    with tab4:
        st.subheader("점포 간 직접 이동 vs DC 경유 이동 비교")

        if transfer_path_result.empty:
            st.warning("점포 간 이동 비교가 가능한 후보가 없습니다.")
        else:
            st.dataframe(transfer_path_result)

            path_summary = (
                transfer_path_result.groupby("recommended_path")
                .size()
                .reset_index(name="count")
            )

            st.write("추천 경로 요약")
            st.dataframe(path_summary)
            st.bar_chart(path_summary.set_index("recommended_path")["count"])

    with tab5:
        st.subheader("프로모션 vs 재배치 비교")

        if promotion_result.empty:
            st.warning("프로모션과 비교할 수 있는 이동 후보가 없습니다.")
        else:
            st.dataframe(promotion_result)

            promo_summary = (
                promotion_result.groupby("final_decision")
                .size()
                .reset_index(name="count")
            )

            st.write("최종 처리 방식 요약")
            st.dataframe(promo_summary)
            st.bar_chart(promo_summary.set_index("final_decision")["count"])

            with st.expander("프로모션 계산식 보기"):
                for _, promo_row in promotion_result.iterrows():
                    st.write(
                        f"{promo_row['product_name']} / "
                        f"{promo_row['source_store']} → {promo_row['target_store']}: "
                        f"{promo_row['promotion_formula']}"
                    )

    with tab6:
        st.subheader("여러 점포 연결 최저비용 경로 계산")

        if network_error:
            st.warning(network_error)
        elif network_path_result.empty:
            st.warning("계산 가능한 다중 연결 경로가 없습니다.")
        else:
            st.dataframe(network_path_result)

            network_summary = (
                network_path_result.groupby("network_recommendation")
                .size()
                .reset_index(name="count")
            )

            st.write("다중 경로 추천 요약")
            st.dataframe(network_summary)
            st.bar_chart(network_summary.set_index("network_recommendation")["count"])

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 실행 분기
# =========================
if st.session_state.selected_mode is None:
    show_mode_selector()
elif st.session_state.selected_mode == "single":
    show_single_calculator()
elif st.session_state.selected_mode == "excel":
    show_excel_optimizer()


