import os
import csv
from datetime import datetime
import textwrap

import streamlit as st
from openai import OpenAI

# ---------- CONFIG ----------

st.set_page_config(
    page_title="SHWIFT Transformation Diagnostic",
    page_icon="✨",
    layout="centered"
)

st.title("✨ SHWIFT Transformation Diagnostic")

st.write(
    "Select your SHWIFT path, answer a focused set of questions, and receive a "
    "**computed Transformation Snapshot** powered by the SHWIFT engine."
)

# 👇 TEMP: show URL query parameters
st.write("DEBUG PARAMS:", st.query_params)

# OpenAI client (expects OPENAI_API_KEY as environment variable or Streamlit secret)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- HELPERS ----------

#def get_tier() -> str:
#    Get tier from URL query params or user selection.
#   query_params = st.query_params
#    default_from_url = query_params.get("tier", "community")

#    tier_label_map = {
#        "community": "SHWIFT Community – Personal growth",
#        "lab": "SHWIFT Lab – Founders & builders",
#        "pro": "SHWIFT Pro – Organisations"
#    }

#    reverse_map = {v: k for k, v in tier_label_map.items()}

#    tier_choice = st.radio(
#        "Choose your SHWIFT path:",
#        options=list(tier_label_map.values()),
#        index=list(tier_label_map.keys()).index(default_from_url)
#        if default_from_url in tier_label_map
#       else 0
#    )

#    return reverse_map[tier_choice]

def get_tier() -> str:
#    Improved tier selector with correct URL handling and safe defaults.

    # 1. Read query params using Streamlit's new API
    params = st.query_params
    default_code = params.get("tier", "community").lower()

    tier_map = {
        "community": "SHWIFT Community – Personal growth",
        "lab": "SHWIFT Lab – Founders & builders",
        "pro": "SHWIFT Pro – Organisations",
    }

    # 2. If ?tier=lab, we map it to label:
    default_label = tier_map.get(default_code, tier_map["community"])

    labels = list(tier_map.values())

    # 3. Radio pre-selects correct tier
    selected_label = st.radio(
        "Choose your SHWIFT path:",
        labels,
        index=labels.index(default_label)
    )

    # 4. Convert label back → short code ("community", "lab", "pro")
    reverse_map = {v: k for k, v in tier_map.items()}
    return reverse_map[selected_label]

def explain_tier(tier: str):
    if tier == "community":
        st.info(
            "You’re entering via **SHWIFT Community** — a space for individuals "
            "in transition who want clarity, momentum, and gentle but focused guidance."
        )
    elif tier == "lab":
        st.info(
            "You’re entering via **SHWIFT Lab** — designed for **founders and builders** "
            "who are shaping products, ventures, or ideas and want sharper execution, "
            "narrative clarity, and better learning loops."
        )
    elif tier == "pro":
        st.info(
            "You’re entering via **SHWIFT Pro** — focused on **organisations**: "
            "strategy clarity, leadership alignment, operating model health, and "
            "transformation readiness."
        )


def build_prompt(tier: str, answers: dict) -> str:
    """
    Build a tier-specific prompt for the SHWIFT engine.
    IMPORTANT: Do not directly mirror or paraphrase user text.
    Treat inputs as data and compute patterns.
    """
    tier = tier.lower()

    if tier == "community":
        base = f"""
You are SHWIFT — a transformation-focused AI engine for individuals.

You receive a short diagnostic from a person and must return a
computed, structured **Transformation Snapshot**.

IMPORTANT STYLE RULES:
- Do NOT copy or closely paraphrase the user's sentences.
- Infer underlying patterns and describe them in your own analytical language.
- Treat the inputs as data points and produce classifications and scores.
- Where helpful, create a short profile name for the person
  (e.g. "Strategic Builder in Transition", "High-Intent Restless Achiever").
- Keep the tone direct, kind, and hopeful.

User data (treat as raw input, not text to echo back):

- 90-day goal: {answers['q1_goal_90']}
- Clarity (1–10): {answers['clarity']}
- Main energy drain: {answers['drain']}
- Defining strength: {answers['strength']}
- Current emotional state: {answers['state']}
- Main reason for delaying tasks: {answers['delay_reason']}
- Pattern to change: {answers['pattern_to_change']}
- Pattern to strengthen: {answers['pattern_to_strengthen']}
- Readiness for change (1–10): {answers['readiness']}

Return your answer in the following sections (as markdown):

1. Profile Name
   - A short 3–6 word label that captures who they are in this season.

2. Identity Pattern (2–3 sentences)
   - Describe their core style and strengths based on the data.

3. Key Blocker (2–3 sentences)
   - Identify the underlying blocker pattern (e.g. stall cycles, emotional overload,
     fear-driven avoidance).

4. Energy & State Reading (2–3 sentences)
   - Interpret their clarity + readiness + emotional state as a computed reading.

5. 90-Day Transformation Focus (3 bullet points)
   - Each bullet is a key lever derived from the data.

6. Recommended First Step (today)
   - One small but meaningful action in the next 24 hours.

7. Key Scores
   - Clarity: X/10 (Low / Medium / High)
   - Readiness: Y/10 (Low / Medium / High)
   - Stall Risk: Low / Medium / High
"""
    elif tier == "lab":
        base = f"""
You are SHWIFT — a transformation-focused AI engine for **founders and builders**.

You receive a short diagnostic from a founder-type person and must return a
computed **Founder Readiness & Focus Map**.

IMPORTANT STYLE RULES:
- Speak like a sharp, concise startup advisor.
- Do NOT mirror their text; interpret it.
- Use founder language: execution, shipping, learning loops, focus, runway, bottlenecks.
- Assume this is an early or mid-stage builder (not a huge corporate).

User data (raw, treat as signals):

- One-line venture description: {answers['one_liner']}
- Target user & problem: {answers['user_problem']}
- Problem pain confidence (1–10): {answers['pain_confidence']}
- Biggest execution bottleneck: {answers['exec_bottleneck']}
- What is stopping progress this week: {answers['blocker_this_week']}
- Hours per week available: {answers['hours_per_week']}
- Founder pattern: {answers['founder_pattern']}
- Runway context: {answers['runway']}
- 30-day success outcome: {answers['day_30_success']}
- Learning speed self-rating (1–10): {answers['learning_speed']}
- Biggest constraint: {answers['biggest_constraint']}
- What they would build if fear wasn't a factor: {answers['no_fear_build']}

Return your answer in the following sections (as markdown):

1. Founder Profile Name
   - E.g. "High-Intent Overthinker", "Reluctant Launcher with Strong Signal".

2. Narrative & Clarity (2–3 sentences)
   - How clear their story and focus appears.

3. Execution Pattern (2–3 sentences)
   - How they execute, where they stall, how hours vs bottlenecks conflict.

4. Learning & Customer Insight (2–3 sentences)
   - How well they appear to learn from cycles and understand users.

5. Key Bottleneck (2–3 sentences)
   - Name the core bottleneck (e.g. "fear of launch", "no prioritisation", "weak discovery").

6. Founder Scores
   - Narrative Clarity: X/10
   - Execution Velocity: X/10
   - Learning Rhythm: X/10
   - Bottleneck Severity: Low / Medium / High

7. 30-Day Build Focus (3 bullet points)
   - What they should focus on for the next 30 days.

8. Recommended Next Move (today)
   - One concrete step they can take in the next 24 hours.
"""
    elif tier == "pro":
        base = f"""
You are SHWIFT — a transformation-focused AI engine for **organisations**.

You receive a short diagnostic from a senior leader (CXO / founder / director) and
must return a computed **Organisational Transformation Snapshot**.

IMPORTANT STYLE RULES:
- Speak like a strategy & transformation consultant (McKinsey / BCG style),
  but in clear language.
- Assume the organisation is real, with teams, processes, customers.
- Do NOT mirror their sentences; infer systemic patterns.
- Focus on: strategy clarity, leadership alignment, execution consistency,
  culture, operating model, risk, and readiness for change.

User data (organisation-level signals):

- One-sentence company strategy: {answers['strategy_sentence']}
- Leadership alignment (1–10): {answers['leadership_alignment']}
- #1 strategic priority (next 12 months): {answers['top_priority']}
- Execution consistency description: {answers['execution_consistency']}
- Customer understanding level: {answers['customer_understanding']}
- Biggest operational bottleneck: {answers['biggest_bottleneck']}
- Role/Responsibility clarity (1–10): {answers['role_clarity']}
- Decision speed description: {answers['decision_speed']}
- Culture description: {answers['culture_description']}
- Change adaptability description: {answers['change_adaptability']}
- Tech/data maturity level: {answers['tech_maturity']}
- Understanding of the "why" behind initiatives: {answers['why_understanding']}
- Where resistance to change shows up: {answers['resistance_areas']}
- Biggest capability gap: {answers['capability_gap']}
- Part of operating model that feels misaligned: {answers['operating_model_issue']}
- Desired outcome next quarter: {answers['quarter_outcome']}
- What would break if nothing changes for 12 months: {answers['break_risk']}
- Leadership commitment level: {answers['leadership_commitment']}

Return your answer in the following sections (as markdown):

1. Organisation Profile Name
   - e.g. "Strategically Clear, Operationally Stalled", "Fragmented Focus in a Changing Market".

2. Strategy & Alignment (2–3 paragraphs)
   - Assess strategy clarity and leadership alignment.

3. Execution & Operating Model (2–3 paragraphs)
   - Assess execution consistency, role clarity, decision speed, bottlenecks.

4. Culture, Change & Capability (2–3 paragraphs)
   - Assess culture, appetite for change, resistance patterns, capability gaps.

5. Risk & Resilience Overview
   - Where this organisation is most at risk if it continues as is.

6. Key Scores
   - Strategy Coherence: X/10
   - Leadership Alignment: X/10
   - Operating Model Health: X/10
   - Culture & Change Readiness: X/10
   - Overall Transformation Readiness: X/10

7. 90-Day Transformation Priorities (3–5 bullets)
   - The most important levers to pull in the next quarter.

8. Executive Recommendation (short)
   - A concise, board-level statement on what must happen next.
"""
    else:
        base = "You are SHWIFT. The tier is unknown. Return a brief message."
    return textwrap.dedent(base).strip()


def call_llm(tier: str, answers: dict) -> str:
    prompt = build_prompt(tier, answers)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": "You are SHWIFT, an AI engine for transformation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Try the simple helper on the new Responses API
    try:
        return response.output_text.strip()
    except AttributeError:
        # Fallback for older / different response shapes
        output_text = ""
        for item in response.output:
            if hasattr(item, "content") and item.content:
                for c in item.content:
                    if hasattr(c, "text") and c.text:
                        output_text += c.text
        return output_text.strip()


# ---------- MAIN UI ----------

tier = get_tier()
explain_tier(tier)

# --- Baseline expectation framing (pre-diagnostic) ---
st.markdown("### Before you begin")
st.caption(
    "This diagnostic offers a snapshot of where you are right now. "
    "It’s designed to prompt clarity and reflection — not to deliver a full solution. "
    "You’ll see optional next steps at the end."
)

begin = st.button("Begin diagnostic")
if not begin:
    st.stop()

st.divider()

with st.form("diagnostic_form"):
    st.subheader("Step 1 – Your Diagnostic")

    if tier == "community":
        # --- COMMUNITY QUESTIONS (individuals) ---
        q1_goal_90 = st.text_area(
            "1. What is your top goal for the next 90 days?",
            placeholder="E.g. Reset my career direction, stabilise my finances, regain emotional clarity…"
        )
        clarity = st.slider(
            "2. How clear do you feel about your direction right now?",
            min_value=1, max_value=10, value=5
        )
        drain = st.selectbox(
            "3. What is draining your energy the most at the moment?",
            [
                "Work stress", "Relationship tension", "Financial pressure",
                "Health / fatigue", "Lack of clarity", "Overwhelm",
                "Fear of failure", "Other / not sure"
            ]
        )
        strength = st.text_input(
            "4. What is one strength that really defines you?",
            placeholder="E.g. Strategic thinking, empathy, persistence, creativity..."
        )
        state = st.selectbox(
            "5. How would you describe your current emotional state?",
            [
                "Calm", "Stressed", "Distracted", "Motivated",
                "Overwhelmed", "Hopeful", "Uncertain", "Exhausted"
            ]
        )
        delay_reason = st.selectbox(
            "6. When you delay tasks, what is usually the main reason?",
            [
                "Fear of doing it wrong",
                "Not sure where to start",
                "Low energy",
                "Distraction",
                "Feeling unmotivated",
                "Feeling incapable",
                "The task feels too big",
                "Emotional avoidance"
            ]
        )
        pattern_to_change = st.text_area(
            "7. What recurring pattern do you most want to change?",
            placeholder="E.g. Overthinking decisions, avoiding difficult conversations, starting but not finishing..."
        )
        pattern_to_strengthen = st.text_area(
            "8. What pattern in you do you want to strengthen or see more of?",
            placeholder="E.g. Following through, staying calm under pressure, daily prayer, learning consistently..."
        )
        readiness = st.slider(
            "9. How ready do you feel for change right now?",
            min_value=1, max_value=10, value=7
        )

        answers = {
            "q1_goal_90": q1_goal_90,
            "clarity": clarity,
            "drain": drain,
            "strength": strength,
            "state": state,
            "delay_reason": delay_reason,
            "pattern_to_change": pattern_to_change,
            "pattern_to_strengthen": pattern_to_strengthen,
            "readiness": readiness,
        }

    elif tier == "lab":
        # --- LAB QUESTIONS (founders & builders) ---
        one_liner = st.text_input(
            "1. In one sentence, what are you building?",
            placeholder="E.g. A tool that helps remote teams run async standups."
        )
        user_problem = st.text_area(
            "2. Who is your user and what problem are you solving right now?",
            placeholder="E.g. Early-stage founders who struggle to prioritise weekly tasks."
        )
        pain_confidence = st.slider(
            "3. How confident are you that this problem is painful enough? (1–10)",
            min_value=1, max_value=10, value=6
        )
        exec_bottleneck = st.selectbox(
            "4. Where is your biggest execution bottleneck at the moment?",
            [
                "Shipping fast",
                "Customer conversations",
                "Technical build",
                "Focus",
                "Market clarity",
                "Prioritisation",
                "Something else"
            ]
        )
        blocker_this_week = st.text_area(
            "5. What is stopping your product or idea from making progress this week?",
            placeholder="E.g. Fear of launching, unclear next step, too many parallel tasks..."
        )
        hours_per_week = st.number_input(
            "6. How many hours per week can you realistically allocate to building?",
            min_value=0, max_value=168, value=10
        )
        founder_pattern = st.selectbox(
            "7. Which pattern best describes you most often?",
            [
                "Overthinking",
                "Overbuilding",
                "Under-talking to customers",
                "Fear of launching",
                "No prioritisation",
                "Burnout loops",
                "None of these / not sure"
            ]
        )
        runway = st.text_input(
            "8. What is your current runway context (if applicable)?",
            placeholder="E.g. 6 months of savings, building alongside a job, funded for 12 months..."
        )
        day_30_success = st.text_area(
            "9. What outcome would make the next 30 days a massive success?",
            placeholder="E.g. 5 real users using the product weekly, or a working prototype tested by 3 customers."
        )
        learning_speed = st.slider(
            "10. How quickly do you typically learn from each build–measure–learn cycle? (1–10)",
            min_value=1, max_value=10, value=7
        )
        biggest_constraint = st.text_area(
            "11. What is the single constraint that scares you the most?",
            placeholder="E.g. Running out of money, never shipping, wrong market..."
        )
        no_fear_build = st.text_area(
            "12. If fear wasn’t a factor, what would you build or launch in the next 7 days?",
            placeholder="Be specific."
        )

        answers = {
            "one_liner": one_liner,
            "user_problem": user_problem,
            "pain_confidence": pain_confidence,
            "exec_bottleneck": exec_bottleneck,
            "blocker_this_week": blocker_this_week,
            "hours_per_week": hours_per_week,
            "founder_pattern": founder_pattern,
            "runway": runway,
            "day_30_success": day_30_success,
            "learning_speed": learning_speed,
            "biggest_constraint": biggest_constraint,
            "no_fear_build": no_fear_build,
        }

    else:
        # --- PRO QUESTIONS (organisations) ---
        strategy_sentence = st.text_input(
            "1. In one sentence, what is your company’s strategy?",
            placeholder="E.g. Become the leading provider of X for Y by doing Z."
        )
        leadership_alignment = st.slider(
            "2. How aligned is your leadership team on this strategy? (1–10)",
            min_value=1, max_value=10, value=6
        )
        top_priority = st.text_input(
            "3. What is your #1 strategic priority for the next 12 months?",
            placeholder="E.g. Expand into a new market, stabilise core operations..."
        )
        execution_consistency = st.text_area(
            "4. How consistently does your organisation execute on agreed priorities?",
            placeholder="Be honest — are priorities followed through or frequently displaced?"
        )
        customer_understanding = st.selectbox(
            "5. How well do you understand your customers’ evolving needs?",
            ["Low", "Medium", "High"]
        )
        biggest_bottleneck = st.selectbox(
            "6. Where is your greatest operational bottleneck right now?",
            [
                "People",
                "Process",
                "Technology",
                "Clarity of direction",
                "Incentives / accountability",
                "Something else"
            ]
        )
        role_clarity = st.slider(
            "7. How clear are roles and responsibilities across teams? (1–10)",
            min_value=1, max_value=10, value=5
        )
        decision_speed = st.text_area(
            "8. How fast can your organisation make key decisions?",
            placeholder="E.g. Weeks of meetings, or decisions made within days..."
        )
        culture_description = st.text_area(
            "9. How would you describe your culture in a sentence or two?",
        )
        change_adaptability = st.text_area(
            "10. How adaptable is your organisation to change?",
            placeholder="E.g. Moves quickly but chaotically, or slow but stable..."
        )
        tech_maturity = st.selectbox(
            "11. What best describes your technology / data maturity?",
            [
                "Very low (mostly manual / spreadsheets)",
                "Emerging (some systems, not integrated)",
                "Developing (core systems in place, gaps remain)",
                "Advanced (integrated platforms, data-driven decisions)"
            ]
        )
        why_understanding = st.text_area(
            "12. How well do teams understand the 'why' behind major initiatives?",
            placeholder="E.g. Only leadership understands, or well-communicated across teams..."
        )
        resistance_areas = st.text_area(
            "13. Where do you see the most resistance to change?",
            placeholder="E.g. Middle management, specific departments, frontline staff..."
        )
        capability_gap = st.text_area(
            "14. What is the biggest capability gap you can see today?",
            placeholder="E.g. Data literacy, leadership depth, product management..."
        )
        operating_model_issue = st.text_area(
            "15. What part of your operating model feels misaligned or outdated?",
            placeholder="E.g. Org structure, incentive model, reporting lines..."
        )
        quarter_outcome = st.text_area(
            "16. What is the most important outcome you want in the next quarter?",
        )
        break_risk = st.text_area(
            "17. If everything stayed the same for 12 months, what would break?",
        )
        leadership_commitment = st.slider(
            "18. How committed is leadership to real transformation? (1–10)",
            min_value=1, max_value=10, value=7
        )

        answers = {
            "strategy_sentence": strategy_sentence,
            "leadership_alignment": leadership_alignment,
            "top_priority": top_priority,
            "execution_consistency": execution_consistency,
            "customer_understanding": customer_understanding,
            "biggest_bottleneck": biggest_bottleneck,
            "role_clarity": role_clarity,
            "decision_speed": decision_speed,
            "culture_description": culture_description,
            "change_adaptability": change_adaptability,
            "tech_maturity": tech_maturity,
            "why_understanding": why_understanding,
            "resistance_areas": resistance_areas,
            "capability_gap": capability_gap,
            "operating_model_issue": operating_model_issue,
            "quarter_outcome": quarter_outcome,
            "break_risk": break_risk,
            "leadership_commitment": leadership_commitment,
        }

    submitted = st.form_submit_button("Generate My SHWIFT Snapshot 🔍")


# ---------- HANDLE SUBMISSION ----------

if submitted:
    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "OPENAI_API_KEY not found. Please set it as an environment variable "
            "or in Streamlit secrets before running this app."
        )
    else:
        with st.spinner("Generating your SHWIFT Transformation Snapshot..."):
            snapshot = call_llm(tier, answers)

        # ✅ (optional but recommended) actually show the snapshot
        st.markdown("### Your SHWIFT Snapshot")
        st.write(snapshot)

        # ✅ post-diagnostic baseline block (NOW correctly scoped)
        st.success("Your SHWIFT Snapshot is ready.")

        st.markdown("### What this snapshot is — and isn’t")
        st.caption(
            "This snapshot highlights patterns, tensions, and signals based on your inputs. "
            "It’s designed to support reflection and clarity — not to prescribe a full solution."
        )

        st.markdown("### Optional next steps")
        st.markdown(
            "- Sit with this snapshot and reflect on what resonates most.\n"
            "- If you’d like guided support, you can explore early access to SHWIFT.\n"
            "- Or simply return later as the ecosystem continues to evolve."
        )

        st.markdown("[Join SHWIFT Early Access →](https://shwift.uk#section02)")

        # keep your logging here too (still indented)
        # log_row = {...}
    

            # Simple logging (local CSV)
        log_row = {
                "timestamp": datetime.utcnow().isoformat(),
                "tier": tier,
                "snapshot_preview": snapshot[:500],
                **{f"input_{k}": str(v) for k, v in answers.items()}
            }
        log_file = "shwift_diagnostic_log.csv"
        file_exists = os.path.isfile(log_file)
        with open(log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=log_row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_row)

        st.subheader("🔍 Your SHWIFT Transformation Snapshot")
        st.markdown(snapshot)

        st.info( 
            "This diagnostic is an early version of the SHWIFT engine. "
            "In future versions, this snapshot will seed a richer Digital Twin "
            "and generate tailored 30–90 day transformation paths for each tier "
            "(Community, Lab, and Pro)."
        )