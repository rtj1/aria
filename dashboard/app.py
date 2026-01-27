"""Streamlit dashboard for ARIA red-teaming agent."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import asyncio

sys.path.insert(0, "..")

from src.agent import ARIAAgent
from src.strategies import STRATEGIES, get_all_strategies
from src.memory import AttackMemory


# Page config
st.set_page_config(
    page_title="ARIA - Red-teaming Dashboard",
    page_icon="🎯",
    layout="wide",
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "attack_history" not in st.session_state:
    st.session_state.attack_history = []
if "memory" not in st.session_state:
    st.session_state.memory = None


def init_agent():
    """Initialize the ARIA agent."""
    if st.session_state.agent is None:
        st.session_state.agent = ARIAAgent(
            use_llm_selection=False,
            use_reflexion=True,
            use_llm_evaluation=True,
        )
        st.session_state.memory = AttackMemory()


def run_attack(behavior: str, strategy: str = None, variant: str = None):
    """Run a single attack and return results."""
    init_agent()
    agent = st.session_state.agent

    # Run attack
    attempt = asyncio.run(agent.attack(
        behavior=behavior,
        strategy_name=strategy if strategy != "Auto" else None,
        variant=variant if variant != "Auto" else None,
    ))

    # Store in memory
    if st.session_state.memory:
        st.session_state.memory.store(
            behavior=attempt.behavior,
            strategy=attempt.strategy_selection.strategy_name,
            variant=attempt.strategy_selection.variant,
            attack_prompt=attempt.attack_result.attack_prompt,
            response=attempt.target_response.content,
            succeeded=attempt.evaluation.attack_succeeded,
            confidence=attempt.evaluation.confidence,
        )

    # Add to history
    st.session_state.attack_history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "behavior": behavior[:50] + "..." if len(behavior) > 50 else behavior,
        "strategy": attempt.strategy_selection.strategy_name,
        "variant": attempt.strategy_selection.variant,
        "succeeded": attempt.evaluation.attack_succeeded,
        "confidence": attempt.evaluation.confidence,
        "latency_ms": attempt.target_response.latency_ms,
    })

    return attempt


# Sidebar
st.sidebar.title("🎯 ARIA")
st.sidebar.caption("Automated Red-teaming & Iterative Attack Agent")

page = st.sidebar.radio(
    "Navigation",
    ["Single Attack", "Campaign", "Results", "Memory", "About"]
)

st.sidebar.divider()

# Strategy info
st.sidebar.subheader("Available Strategies")
for name, cls in STRATEGIES.items():
    instance = cls()
    with st.sidebar.expander(f"📌 {name}"):
        st.write(instance.description)
        st.caption(f"Variants: {len(instance.variants)}")


# Main content
if page == "Single Attack":
    st.title("🎯 Single Attack")
    st.caption("Test a single attack against Claude")

    col1, col2 = st.columns([2, 1])

    with col1:
        behavior = st.text_area(
            "Target Behavior",
            placeholder="Enter the forbidden behavior you want to elicit...",
            help="Describe what you want the model to do (that it shouldn't)",
            height=100,
        )

    with col2:
        strategy = st.selectbox(
            "Strategy",
            ["Auto"] + list(STRATEGIES.keys()),
            help="Select a specific strategy or let ARIA choose",
        )

        if strategy != "Auto":
            strategy_instance = STRATEGIES[strategy]()
            variant = st.selectbox(
                "Variant",
                ["Auto"] + strategy_instance.variants,
            )
        else:
            variant = "Auto"

    if st.button("🚀 Launch Attack", type="primary", use_container_width=True):
        if not behavior:
            st.error("Please enter a target behavior")
        else:
            with st.spinner("Executing attack..."):
                attempt = run_attack(behavior, strategy, variant)

            # Results
            st.divider()

            if attempt.evaluation.attack_succeeded:
                st.success(f"✅ Attack SUCCEEDED (confidence: {attempt.evaluation.confidence:.2%})")
            else:
                st.error(f"❌ Attack FAILED (confidence: {attempt.evaluation.confidence:.2%})")

            col1, col2, col3 = st.columns(3)
            col1.metric("Strategy", attempt.strategy_selection.strategy_name)
            col2.metric("Variant", attempt.strategy_selection.variant)
            col3.metric("Latency", f"{attempt.target_response.latency_ms:.0f}ms")

            with st.expander("📝 Attack Prompt", expanded=False):
                st.code(attempt.attack_result.attack_prompt, language=None)

            with st.expander("💬 Model Response", expanded=True):
                st.write(attempt.target_response.content)

            if attempt.reflexion:
                with st.expander("🧠 Reflexion", expanded=False):
                    st.write(attempt.reflexion)


elif page == "Campaign":
    st.title("🎯 Attack Campaign")
    st.caption("Run multiple attacks against a list of behaviors")

    behaviors_input = st.text_area(
        "Target Behaviors (one per line)",
        placeholder="Enter each behavior on a new line...",
        height=150,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        strategies = st.multiselect(
            "Strategies",
            list(STRATEGIES.keys()),
            default=list(STRATEGIES.keys()),
        )

    with col2:
        max_attempts = st.number_input(
            "Max attempts per behavior",
            min_value=1,
            max_value=20,
            value=5,
        )

    with col3:
        stop_on_success = st.checkbox("Stop on success", value=True)

    if st.button("🚀 Start Campaign", type="primary", use_container_width=True):
        behaviors = [b.strip() for b in behaviors_input.strip().split("\n") if b.strip()]

        if not behaviors:
            st.error("Please enter at least one behavior")
        elif not strategies:
            st.error("Please select at least one strategy")
        else:
            init_agent()
            agent = st.session_state.agent

            progress_bar = st.progress(0)
            status_text = st.empty()

            total = len(behaviors) * max_attempts
            completed = 0
            results = []

            for behavior in behaviors:
                for strategy_name in strategies:
                    strategy = STRATEGIES[strategy_name]()
                    for variant in strategy.variants[:max_attempts]:
                        status_text.text(f"Testing: {strategy_name}/{variant}")

                        attempt = asyncio.run(agent.attack(
                            behavior=behavior,
                            strategy_name=strategy_name,
                            variant=variant,
                        ))

                        results.append({
                            "behavior": behavior[:30],
                            "strategy": strategy_name,
                            "variant": variant,
                            "succeeded": attempt.evaluation.attack_succeeded,
                            "confidence": attempt.evaluation.confidence,
                        })

                        completed += 1
                        progress_bar.progress(completed / total)

                        if stop_on_success and attempt.evaluation.attack_succeeded:
                            break
                    if stop_on_success and results and results[-1]["succeeded"]:
                        break

            status_text.text("Campaign complete!")

            # Show results
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            # Summary
            total_attacks = len(results)
            successful = sum(1 for r in results if r["succeeded"])
            st.metric(
                "Overall ASR",
                f"{successful}/{total_attacks} ({successful/total_attacks:.1%})"
            )


elif page == "Results":
    st.title("📊 Results & Metrics")

    init_agent()
    agent = st.session_state.agent

    if not st.session_state.attack_history:
        st.info("No attacks run yet. Go to 'Single Attack' or 'Campaign' to start.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total = len(st.session_state.attack_history)
        successful = sum(1 for a in st.session_state.attack_history if a["succeeded"])

        col1.metric("Total Attacks", total)
        col2.metric("Successful", successful)
        col3.metric("ASR", f"{successful/total:.1%}" if total > 0 else "0%")
        col4.metric("Avg Latency", f"{sum(a['latency_ms'] for a in st.session_state.attack_history)/total:.0f}ms" if total > 0 else "0ms")

        st.divider()

        # Attack history table
        st.subheader("Attack History")
        df = pd.DataFrame(st.session_state.attack_history)
        st.dataframe(df, use_container_width=True)

        # ASR by strategy chart
        if agent and agent.metrics.total_attacks > 0:
            st.subheader("ASR by Strategy")
            asr_data = agent.metrics.asr_by_strategy()

            if asr_data:
                fig = px.bar(
                    x=list(asr_data.keys()),
                    y=[v * 100 for v in asr_data.values()],
                    labels={"x": "Strategy", "y": "ASR (%)"},
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

        # Success over time
        st.subheader("Success Over Time")
        if st.session_state.attack_history:
            cumulative_success = []
            total_so_far = 0
            success_so_far = 0
            for attack in st.session_state.attack_history:
                total_so_far += 1
                if attack["succeeded"]:
                    success_so_far += 1
                cumulative_success.append(success_so_far / total_so_far * 100)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=cumulative_success,
                mode='lines+markers',
                name='Cumulative ASR',
            ))
            fig.update_layout(
                yaxis_title="ASR (%)",
                xaxis_title="Attack #",
                yaxis_range=[0, 100],
            )
            st.plotly_chart(fig, use_container_width=True)


elif page == "Memory":
    st.title("🧠 Attack Memory")

    init_agent()
    memory = st.session_state.memory

    if memory:
        stats = memory.get_stats()

        col1, col2, col3 = st.columns(3)
        col1.metric("Successful Attacks", stats["successful_attacks"])
        col2.metric("Failed Attacks", stats["failed_attacks"])
        col3.metric("Total Stored", stats["total_attacks"])

        st.divider()

        st.subheader("Find Similar Attacks")
        query = st.text_input("Enter a behavior to find similar attacks")

        if query:
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Successful Similar Attacks:**")
                similar_success = memory.find_similar_successful(query, n_results=3)
                for attack in similar_success:
                    with st.expander(f"✅ {attack.strategy}/{attack.variant}"):
                        st.write(f"**Behavior:** {attack.behavior}")
                        st.code(attack.attack_prompt[:300])

            with col2:
                st.write("**Failed Similar Attacks:**")
                similar_failed = memory.find_similar_failed(query, n_results=3)
                for attack in similar_failed:
                    with st.expander(f"❌ {attack.strategy}/{attack.variant}"):
                        st.write(f"**Behavior:** {attack.behavior}")
                        st.code(attack.attack_prompt[:300])

        if st.button("🗑️ Clear Memory", type="secondary"):
            memory.clear()
            st.success("Memory cleared!")
            st.rerun()
    else:
        st.info("Memory not initialized. Run some attacks first.")


elif page == "About":
    st.title("ℹ️ About ARIA")

    st.markdown("""
    ## Automated Red-teaming & Iterative Attack Agent

    ARIA is a research tool for automated LLM red-teaming, designed to:

    1. **Generate adversarial prompts** using multiple attack strategies
    2. **Test against target models** (currently Claude)
    3. **Evaluate responses** to determine attack success
    4. **Learn from failures** using the Reflexion pattern
    5. **Track metrics** across attack campaigns

    ### Attack Strategies

    | Strategy | Description | Expected ASR |
    |----------|-------------|--------------|
    | Roleplay | Fictional scenarios to deflect responsibility | ~89% |
    | Logic Trap | Logical contradictions and reasoning tricks | ~81% |
    | Encoding | Base64, ROT13, and other encodings | ~76% |
    | Prefix Injection | Response format manipulation | ~70% |
    | Hypothetical | Thought experiments and what-ifs | ~65% |

    ### Ethical Use

    This tool is for **authorized security research only**.

    - Use only on systems you have permission to test
    - Document findings responsibly
    - Report vulnerabilities through proper channels
    - Do not use for malicious purposes

    ### Research Context

    Built as part of preparation for the Anthropic Security Fellow program.
    The goal is to understand LLM vulnerabilities to help build safer AI systems.

    ---

    *ARIA - For Anthropic Security Fellow Application*
    """)


# Footer
st.sidebar.divider()
st.sidebar.caption("ARIA v0.1.0 | Built for AI Security Research")
