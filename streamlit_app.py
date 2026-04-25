from __future__ import annotations

import traceback
import uuid

import streamlit as st

from app.config import settings
from app.demo_service import DemoService, FeatureFlags


st.set_page_config(
    page_title="Redis + OpenShift AI Defense Demo",
    page_icon=":satellite:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def get_demo_service() -> DemoService:
    service = DemoService()
    service.bootstrap()
    return service


def init_session_state() -> None:
    defaults = {
        "baseline_messages": [],
        "enhanced_messages": [],
        "baseline_last_result": None,
        "enhanced_last_result": None,
        "baseline_error": None,
        "enhanced_error": None,
        "baseline_input": "",
        "enhanced_input": "",
        "enhanced_session_id": uuid.uuid4().hex[:12],
        "enhanced_metrics": {"cache_hits": 0, "tokens_saved": 0, "cost_saved": 0.0},
        "enhanced_feature_semantic_cache": False,
        "enhanced_feature_memory": False,
        "enhanced_feature_rag": False,
        "enhanced_feature_routing": False,
        "enhanced_ingested_uploads": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_error(container, message: str, details: str) -> None:
    container.error(message)
    with container.expander("Technical details"):
        st.code(details)


def inject_branding_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --redis-ink: #1f2937;
          --redis-surface: #f7f4ef;
          --redis-surface-strong: #fffdf8;
          --redis-stroke: #e6ded1;
          --redis-primary: #a41e22;
          --redis-primary-dark: #7f1316;
          --redis-accent: #2b6cb0;
          --redis-accent-soft: #dceefe;
          --redhat-accent: #ee0000;
          --redhat-accent-soft: rgba(238, 0, 0, 0.08);
          --success-soft: #e6f7ef;
          --shadow-soft: 0 18px 45px rgba(31, 41, 55, 0.08);
          --radius-xl: 24px;
          --radius-lg: 18px;
          --radius-md: 14px;
        }

        .stApp {
          background:
            radial-gradient(circle at top right, rgba(43, 108, 176, 0.08), transparent 28%),
            linear-gradient(180deg, #fbfaf7 0%, #f4efe7 100%);
          color: var(--redis-ink);
        }

        [data-testid="stSidebar"] {
          display: none;
        }

        .block-container {
          padding-top: 2rem;
          padding-bottom: 2rem;
        }

        .brand-shell {
          border: 1px solid var(--redis-stroke);
          background: linear-gradient(135deg, rgba(164, 30, 34, 0.06), rgba(255, 255, 255, 0.9));
          border-radius: var(--radius-xl);
          padding: 1.5rem 1.75rem;
          box-shadow: var(--shadow-soft);
          margin-bottom: 1rem;
        }

        .brand-title {
          font-size: 2.2rem;
          font-weight: 700;
          letter-spacing: -0.03em;
          margin: 0;
          color: var(--redis-ink);
        }

        .brand-subtitle {
          margin: 0.5rem 0 0;
          color: rgba(31, 41, 55, 0.75);
          font-size: 1rem;
          max-width: 64rem;
        }

        .brand-chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.6rem;
          margin-top: 1rem;
        }

        .brand-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          padding: 0.45rem 0.8rem;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.88);
          border: 1px solid var(--redis-stroke);
          font-size: 0.87rem;
          color: var(--redis-ink);
        }

        .brand-chip strong {
          color: var(--redis-primary-dark);
        }

        .panel-card {
          border: 1px solid var(--redis-stroke);
          background: rgba(255, 255, 255, 0.86);
          border-radius: var(--radius-xl);
          padding: 1rem 1rem 1.2rem;
          box-shadow: var(--shadow-soft);
          min-height: 100%;
        }

        .panel-card.baseline {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(247, 244, 239, 0.95));
        }

        .panel-card.enhanced {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(220, 238, 254, 0.28));
          border-color: rgba(43, 108, 176, 0.22);
        }

        .panel-kicker {
          display: inline-flex;
          align-items: center;
          padding: 0.32rem 0.7rem;
          border-radius: 999px;
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          margin-bottom: 0.75rem;
        }

        .panel-kicker.baseline {
          background: rgba(31, 41, 55, 0.08);
          color: var(--redis-ink);
        }

        .panel-kicker.enhanced {
          background: var(--redis-accent-soft);
          color: var(--redis-accent);
        }

        .section-card {
          border: 1px solid var(--redis-stroke);
          background: var(--redis-surface-strong);
          border-radius: var(--radius-lg);
          padding: 0.85rem 1rem;
          margin-top: 0.9rem;
        }

        .section-card.controls {
          border-left: 4px solid var(--redis-accent);
        }

        .section-card.telemetry {
          border-left: 4px solid var(--redhat-accent);
        }

        div[data-testid="stTextArea"] textarea {
          border-radius: var(--radius-md);
          border: 1px solid var(--redis-stroke);
          background: rgba(255, 253, 248, 0.95);
        }

        div[data-testid="stTextArea"] textarea:focus {
          border-color: var(--redis-accent);
          box-shadow: 0 0 0 1px var(--redis-accent);
        }

        .stButton > button,
        div[data-testid="stFormSubmitButton"] button {
          background: linear-gradient(135deg, var(--redis-primary), var(--redis-primary-dark));
          color: white;
          border: none;
          border-radius: 999px;
          font-weight: 700;
          padding: 0.55rem 1rem;
          box-shadow: 0 10px 24px rgba(164, 30, 34, 0.18);
        }

        .stButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
          background: linear-gradient(135deg, var(--redis-primary-dark), var(--redis-primary));
        }

        div[data-testid="stFileUploader"] section {
          border-radius: var(--radius-md);
          border: 1px dashed var(--redis-accent);
          background: rgba(220, 238, 254, 0.24);
        }

        div[data-testid="stMetric"] {
          background: rgba(255, 255, 255, 0.86);
          border: 1px solid var(--redis-stroke);
          border-radius: var(--radius-md);
          padding: 0.6rem 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        f"""
        <div class="brand-shell">
          <p class="brand-title">Redis Mission Assistant</p>
          <p class="brand-subtitle">
            Compare a direct baseline LLM experience with a Redis-enhanced workflow using a Redis-led interface
            and restrained Red Hat accents for enterprise framing.
          </p>
          <div class="brand-chip-row">
            <span class="brand-chip"><strong>LLM</strong> {settings.llm_api_format}</span>
            <span class="brand-chip"><strong>Embeddings</strong> {settings.embedding_api_format}</span>
            <span class="brand-chip"><strong>Vector Index</strong> {settings.vector_index_name}</span>
            <span class="brand-chip"><strong>Enhanced Session</strong> {st.session_state.enhanced_session_id}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_messages(container, messages: list[dict[str, str]], empty_text: str) -> None:
    with container:
        if not messages:
            st.info(empty_text)
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def render_enhanced_telemetry(container, features: FeatureFlags) -> None:
    result = st.session_state.enhanced_last_result
    if not result:
        container.caption("Enhanced telemetry will appear after you send a message.")
        return

    container.markdown("#### Telemetry")
    container.write(f"**LLM latency:** {result.llm_latency_ms:.1f} ms")
    container.write(f"**Estimated total tokens:** {result.total_tokens}")
    if features.routing:
        container.write(f"**Route selected:** `{result.route.route}`")
        container.write(f"**Route rationale:** {result.route.rationale}")
    if features.semantic_cache:
        container.write(f"**Cache status:** {'Hit' if result.used_cache else 'Miss'}")
        if result.cache.hit:
            container.success(
                f"Semantic cache hit. Saved ~{result.cache.tokens_saved} tokens and "
                f"${result.cache.cost_saved:.4f}."
            )
    if features.semantic_cache or features.rag_context:
        container.write(f"**Embedding latency:** {result.embedding_latency_ms:.1f} ms")
    if features.memory:
        memory = result.memory_summary
        container.write(f"**Memory turns retained:** {memory['turns']}")
        container.write(f"**Memory token estimate:** {memory['estimated_tokens']}")
        container.caption(memory["preview"] or "No memory yet.")
    if features.rag_context:
        container.write("**Retrieved evidence:**")
        if result.retrieval_matches:
            for match in result.retrieval_matches:
                container.markdown(
                    f"- `{match.title or match.source}` | score `{match.score:.4f}`\n\n  {match.text[:180]}..."
                )
        else:
            container.caption("No retrieval context used for the last answer.")


def render_baseline_telemetry(container) -> None:
    result = st.session_state.baseline_last_result
    if not result:
        container.caption("Baseline telemetry will appear after you send a message.")
        return

    container.markdown("#### Telemetry")
    container.write(f"**LLM latency:** {result.llm_latency_ms:.1f} ms")
    container.write(f"**Estimated total tokens:** {result.total_tokens}")


def enhanced_feature_flags() -> FeatureFlags:
    return FeatureFlags(
        semantic_cache=st.session_state.enhanced_feature_semantic_cache,
        memory=st.session_state.enhanced_feature_memory,
        rag_context=st.session_state.enhanced_feature_rag,
        routing=st.session_state.enhanced_feature_routing,
    )


def process_baseline_submit(service: DemoService) -> None:
    prompt = st.session_state.baseline_input.strip()
    if not prompt:
        return
    st.session_state.baseline_messages.append({"role": "user", "content": prompt})
    try:
        result = service.ask(session_id="baseline", question=prompt, features=FeatureFlags())
    except Exception as exc:
        st.session_state.baseline_error = (f"Unable to get a baseline response: {exc}", traceback.format_exc())
        return
    st.session_state.baseline_last_result = result
    st.session_state.baseline_messages.append({"role": "assistant", "content": result.answer})
    st.session_state.baseline_error = None


def process_enhanced_submit(service: DemoService) -> None:
    prompt = st.session_state.enhanced_input.strip()
    if not prompt:
        return
    features = enhanced_feature_flags()
    st.session_state.enhanced_messages.append({"role": "user", "content": prompt})
    try:
        result = service.ask(
            session_id=st.session_state.enhanced_session_id,
            question=prompt,
            features=features,
        )
    except Exception as exc:
        st.session_state.enhanced_error = (f"Unable to get an enhanced response: {exc}", traceback.format_exc())
        return
    st.session_state.enhanced_last_result = result
    st.session_state.enhanced_messages.append({"role": "assistant", "content": result.answer})
    st.session_state.enhanced_error = None
    if result.cache.hit:
        st.session_state.enhanced_metrics["cache_hits"] += 1
        st.session_state.enhanced_metrics["tokens_saved"] += result.cache.tokens_saved
        st.session_state.enhanced_metrics["cost_saved"] += result.cache.cost_saved


def handle_enhanced_uploads(service: DemoService, container) -> None:
    uploads = container.file_uploader(
        "Upload files for the enhanced panel",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        key="enhanced_uploads",
    )
    if not uploads:
        return
    known_uploads = set(st.session_state.enhanced_ingested_uploads)
    for upload in uploads:
        upload_id = f"{upload.name}:{upload.size}"
        if upload_id in known_uploads:
            continue
        try:
            result = service.ingest_uploaded_file(st.session_state.enhanced_session_id, upload)
        except Exception as exc:
            render_error(container, f"Unable to ingest {upload.name}.", traceback.format_exc())
            break
        else:
            container.success(f"Ingested {upload.name}: {result.chunks} chunks")
            known_uploads.add(upload_id)
    st.session_state.enhanced_ingested_uploads = sorted(known_uploads)


def main() -> None:
    init_session_state()
    service = get_demo_service()
    inject_branding_styles()
    render_header()

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown('<div class="panel-card baseline">', unsafe_allow_html=True)
        st.markdown('<div class="panel-kicker baseline">Baseline LLM</div>', unsafe_allow_html=True)
        st.subheader("Direct Chat")
        st.caption("A neutral baseline path that uses the same model and system prompt without Redis-backed features.")
        with st.form("baseline_form", clear_on_submit=True):
            st.text_area(
                "Message",
                key="baseline_input",
                placeholder="Ask the baseline model a question...",
                height=80,
            )
            baseline_submitted = st.form_submit_button("Send to Baseline", use_container_width=True)
        if baseline_submitted:
            with st.spinner("Baseline chat is generating a response..."):
                process_baseline_submit(service)
        baseline_messages = st.container(height=420)
        render_messages(
            baseline_messages,
            st.session_state.baseline_messages,
            "Send a message to test the baseline LLM flow.",
        )
        if st.session_state.baseline_error:
            message, details = st.session_state.baseline_error
            render_error(st, message, details)
        st.markdown('<div class="section-card telemetry">', unsafe_allow_html=True)
        baseline_telemetry = st.container()
        render_baseline_telemetry(baseline_telemetry)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="panel-card enhanced">', unsafe_allow_html=True)
        st.markdown('<div class="panel-kicker enhanced">Redis Enhanced</div>', unsafe_allow_html=True)
        st.subheader("Configurable Redis Workflow")
        st.caption("Enable Redis-backed features selectively to compare caching, memory, routing, and retrieval.")
        with st.form("enhanced_form", clear_on_submit=True):
            st.text_area(
                "Message",
                key="enhanced_input",
                placeholder="Ask the enhanced model a question...",
                height=80,
            )
            enhanced_submitted = st.form_submit_button("Send to Enhanced", use_container_width=True)
        if enhanced_submitted:
            with st.spinner("Enhanced chat is processing with the selected features..."):
                process_enhanced_submit(service)
        enhanced_messages = st.container(height=420)
        render_messages(
            enhanced_messages,
            st.session_state.enhanced_messages,
            "Send a message or upload a file to test the enhanced flow.",
        )
        st.markdown('<div class="section-card controls">', unsafe_allow_html=True)
        feature_box = st.container()
        with feature_box:
            st.markdown("#### Enhanced Features")
            st.toggle("Semantic caching", key="enhanced_feature_semantic_cache")
            st.toggle("Memory", key="enhanced_feature_memory")
            st.toggle("RAG context", key="enhanced_feature_rag")
            st.toggle("Routing", key="enhanced_feature_routing")
            if st.button("Clear Enhanced Memory", use_container_width=True):
                try:
                    service.clear_memory(st.session_state.enhanced_session_id)
                except Exception as exc:
                    render_error(st, f"Unable to clear enhanced memory: {exc}", traceback.format_exc())
                else:
                    st.success("Enhanced memory cleared.")
            handle_enhanced_uploads(service, st)
            metrics = st.session_state.enhanced_metrics
            st.caption(
                f"Cache hits: {metrics['cache_hits']} | Tokens saved: {metrics['tokens_saved']} | "
                f"Estimated cost saved: ${metrics['cost_saved']:.4f}"
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="section-card telemetry">', unsafe_allow_html=True)
        render_enhanced_telemetry(st.container(), enhanced_feature_flags())
        st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.enhanced_error:
            message, details = st.session_state.enhanced_error
            render_error(st, message, details)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
