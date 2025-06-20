import streamlit as st
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os

# ------------------- Load Environment Variables -------------------
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")  # Fallback to local

# ------------------- OpenAI Client -------------------
gpt = OpenAI(api_key=openai_key)

# ------------------- Page Config & Styling -------------------
st.set_page_config(page_title="Investment Assistant for Migrants ", layout="centered")

st.markdown("""
    <style>
        .title-style {
            font-size: 30px;
            font-weight: bold;
            color: #2C3E50;
            text-align: center;
            padding: 10px 0;
        }
        .stRadio > div {
            flex-direction: row;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-style">📊 Personalized Investment Planner for U.S. Migrants from entire world</div>', unsafe_allow_html=True)

# ------------------- Main Form -------------------
st.markdown("### 👤 Tell us about yourself:")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=18, max_value=100, help="Your current age.")
    income = st.number_input("Annual Income (USD)", min_value=10000, step=5000)
    visa_status = st.selectbox("Visa Status", ["OPT", "H1B", "Green Card", "Citizen", "Other"])
    remittance = st.radio("Do you send money to your home country?", ["Yes", "No"])

with col2:
    risk = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"], help="How comfortable are you with investment risk?")
    goal = st.selectbox("Investment Goal", ["Retirement", "Wealth Growth", "Emergency Fund", "Education", "Buy a House", "Support Family"])
    default_duration = "Short Term (<3 years)" if visa_status == "OPT" else "Medium Term (3–10 years)"
    duration = st.selectbox("Investment Horizon", ["Short Term (<3 years)", "Medium Term (3–10 years)", "Long Term (10+ years)"],
                            index=["Short Term (<3 years)", "Medium Term (3–10 years)", "Long Term (10+ years)"].index(default_duration))

sectors = st.multiselect("Preferred Sectors (Optional)", ["Technology", "Healthcare", "Energy", "Finance", "Real Estate", "Consumer Goods"])
query = st.text_area("What would you like help with?", "How should I invest monthly to reach my retirement goal?")
monthly_sip = st.number_input("Monthly Investment Amount (USD)", min_value=0, step=10, help="Leave 0 if you want the assistant to suggest a suitable amount.")

# ------------------- Session State -------------------
if 'last_response' not in st.session_state:
    st.session_state['last_response'] = ""

# ------------------- Generate Plan -------------------
if st.button("📥 Generate My Investment Plan"):
    with st.spinner("Working on your personalized investment strategy..."):
        payload = {
            "age": age,
            "income": income,
            "risk": risk,
            "goal": goal,
            "duration": duration,
            "sectors": sectors,
            "query": query,
            "monthly_sip": monthly_sip if monthly_sip > 0 else None,
            "visa_status": visa_status,
            "remittance": remittance == "Yes"
        }

        try:
            res = requests.post(f"{BACKEND_URL}/invest", json=payload)
            res.raise_for_status()
            result = res.json()["response"]

            st.session_state['last_response'] = result
            st.success("✅ Here's your personalized investment strategy:")
            st.markdown(result)

        except Exception as e:
            st.error(f"❌ Could not generate plan: {str(e)}")

# ------------------- Sidebar: Follow-up -------------------
st.sidebar.markdown("### 🤖 Ask a Follow-up")
followup = st.sidebar.text_input("Have more questions?")

if followup:
    if not st.session_state['last_response']:
        st.sidebar.warning("⚠️ Please generate a plan first.")
    else:
        try:
            followup_reply = gpt.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a friendly financial assistant helping U.S.-based migrants."},
                    {"role": "user", "content": f"The user got this advice:\n\n{st.session_state['last_response']}\n\nNow they ask: {followup}"}
                ],
                temperature=0.5,
                max_tokens=400
            )
            st.sidebar.markdown("#### 💡 Answer:")
            st.sidebar.write(followup_reply.choices[0].message.content)
        except Exception as e:
            st.sidebar.error(f"❌ Could not get follow-up response: {str(e)}")

# ------------------- Investment History -------------------
st.markdown("---")
st.markdown("### 📚 Your Recent Investment Plans")

if st.button("📖 Show My Last 10 Plans"):
    try:
        res = requests.get(f"{BACKEND_URL}/history")
        res.raise_for_status()
        history_data = res.json()

        if history_data:
            for i, plan in enumerate(history_data, start=1):
                st.markdown(f"#### 📌 Plan #{i}")
                st.markdown(f"- **Age:** {plan['age']}")
                st.markdown(f"- **Income:** ${plan['income']:,}")
                st.markdown(f"- **Monthly SIP:** ${plan['sip']:,}")
                st.markdown(f"- **Risk Tolerance:** {plan['risk']}")
                st.markdown(f"- **Goal:** {plan['goal']}")
                st.markdown(f"- **Timestamp:** {plan['timestamp']}")
                st.markdown("**Query:**")
                st.code(plan['query'])
                st.markdown("**Advisor Response:**")
                st.code(plan['response'], language="markdown")
                st.markdown("---")
        else:
            st.info("You don't have any past plans yet.")

    except Exception as e:
        st.error(f"❌ Failed to fetch history: {str(e)}")
