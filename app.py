import streamlit as st
from calculator import calculate_inventory_analysis
from discount_analyzer import analyze_discount_options

st.set_page_config(page_title="편의점 악성재고 계산기", layout="wide")

st.title("편의점 악성재고 처리 의사결정 프로그램")
st.write("수치를 직접 입력하면 악성재고 여부, 처리 결과, 계산 방식을 자동으로 보여줍니다.")

st.sidebar.header("입력값 설정")

store_name = st.sidebar.text_input("점포명", "강남점")
product_name = st.sidebar.text_input("상품명", "삼각김밥")

stock_qty = st.sidebar.number_input("현재 재고 수량", min_value=0, value=100)
sales_30d = st.sidebar.number_input("최근 30일 판매량", min_value=0, value=5)
inbound_days = st.sidebar.number_input("입고 후 지난 일수", min_value=0, value=50)

unit_cost = st.sidebar.number_input("상품 1개당 원가(원)", min_value=0, value=1500)
daily_holding_cost = st.sidebar.number_input("하루 보관비(원)", min_value=0, value=20)
disposal_cost_per_unit = st.sidebar.number_input("상품 1개당 폐기비용(원)", min_value=0, value=300)

discount_rate = st.sidebar.number_input("할인율(%)", min_value=0.0, max_value=100.0, value=20.0)
expected_sales_increase_rate = st.sidebar.number_input("할인 시 판매 증가율(%)", min_value=0.0, value=50.0)

transfer_possible = st.sidebar.selectbox("타점포 이동 가능 여부", ["가능", "불가능"])
distance_km = st.sidebar.number_input("점포 간 거리(km)", min_value=0.0, value=10.0)
cost_per_km = st.sidebar.number_input("km당 운송비(원)", min_value=0.0, value=500.0)
target_store_sales_30d = st.sidebar.number_input("이동 대상 점포 최근 30일 판매량", min_value=0, value=20)

if st.button("계산 시작"):
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

    st.subheader("입력 정보")
    st.write(f"점포명: {store_name}")
    st.write(f"상품명: {product_name}")

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

        st.subheader("비용 비교")
    st.write(f"유지 비용: {result['keep_cost']}원")
    st.write(f"할인 전략 순비용: {result['discount_net_cost']}원")

    if result["transfer_net_cost"] is not None:
        st.write(f"자동 계산된 이동비: {result['transfer_cost']}원")
        st.write(f"타점포 이동 순비용: {result['transfer_net_cost']}원")
        st.write(f"폐기 비용: {result['disposal_cost']}원")
        cost_data = {
            "전략": ["유지", "할인", "타점포 이동", "폐기"],
            "비용": [
                result["keep_cost"],
                result["discount_net_cost"],
                result["transfer_net_cost"],
                result["disposal_cost"],
            ],
        }
    else:
        st.write("타점포 이동 순비용: 이동 불가능")
        cost_data = {
            "전략": ["유지", "할인", "폐기"],
            "비용": [
                result["keep_cost"],
                result["discount_net_cost"],
                result["disposal_cost"],
            ],
        }

    st.bar_chart(data=cost_data, x="전략", y="비용")

    st.subheader("최종 추천")
    st.write(f"추천 전략: **{result['best_action']}**")
    st.write(f"추천 이유: {result['recommendation_reason']}")
    st.write(f"발주 조언: **{result['order_advice']}**")

    st.subheader("할인율별 비교")
    st.dataframe(discount_comparison)

    discount_chart_data = {
        "할인율": [f"{item['discount_rate']}%" for item in discount_comparison],
        "순비용": [item["net_cost"] for item in discount_comparison],
    }

    st.bar_chart(discount_chart_data, x="할인율", y="순비용")

    st.subheader("계산 방식")
    st.write(result["formula_text"]["stock_cover_days_formula"])
    st.write(result["formula_text"]["risk_formula"])
    st.write(result["formula_text"]["keep_cost_formula"])
    st.write(result["formula_text"]["discount_formula"])
    st.write(result["formula_text"]["transfer_formula"])
    st.write(result["formula_text"]["disposal_formula"])

    st.markdown("---")
st.caption("© 2026 김서호. All rights reserved.")