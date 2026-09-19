"""Streamlit UI. All knowledge retrieval goes through search_backend.search."""

import streamlit as st

import search_backend


st.set_page_config(page_title="Company Knowledge Brain", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:wght@500;600;700&display=swap');

        :root {
            --ink: #1b2a26;
            --muted: #68716d;
            --paper: #f1eee5;
            --card: #fbfaf6;
            --line: #c8c4b7;
            --accent: #b55b35;
            --accent-soft: #f1ddd3;
            --path: #9f4c2c;
            --path-soft: #f1ddd3;
        }

        .stApp {
            background: var(--paper);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1040px;
            padding-top: 4.5rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
            font-family: 'DM Sans', sans-serif;
        }

        h1 {
            color: var(--ink);
            font-family: 'Source Serif 4', serif !important;
            font-size: clamp(2.6rem, 5vw, 4.4rem) !important;
            font-weight: 600 !important;
            letter-spacing: -0.045em;
            line-height: 0.98;
            margin-bottom: 0.55rem !important;
            text-wrap: balance;
        }

        h2, h3 {
            color: var(--ink);
            border-bottom: 1px solid var(--line);
            font-family: 'Source Serif 4', serif !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
            padding-bottom: 0.45rem;
            text-wrap: balance;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        [data-testid="stTextInput"] label {
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 600;
        }

        [data-testid="stTextInput"] input {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 2px;
            color: var(--ink);
            font-family: 'DM Sans', sans-serif;
            font-size: 1rem;
            min-height: 3.4rem;
            padding: 0.7rem 1rem;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(181, 91, 53, 0.18);
        }

        [data-testid="stButton"] button {
            background: var(--accent);
            border: 1px solid var(--accent);
            border-radius: 2px;
            color: #fbfaf6;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.92rem;
            font-weight: 600;
            min-height: 3.4rem;
            padding: 0.7rem 1.15rem;
        }

        [data-testid="stButton"] button:hover {
            background: var(--path);
            border-color: var(--path);
            color: #fbfaf6;
        }

        [data-testid="stButton"] button:focus-visible {
            box-shadow: 0 0 0 3px rgba(181, 91, 53, 0.22);
        }

        [data-testid="stButton"] button:active {
            transform: translateY(1px);
        }

        .hero-kicker {
            color: var(--accent);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.76rem;
            font-weight: 500;
            letter-spacing: 0.02em;
            margin-bottom: 0.45rem;
        }

        .answer-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-left: 4px solid var(--accent);
            border-radius: 2px;
            color: var(--ink);
            font-family: 'Source Serif 4', serif;
            font-size: 1.18rem;
            line-height: 1.58;
            padding: 1.35rem 1.45rem;
        }

        .source-row {
            align-items: center;
            background: transparent;
            border-bottom: 1px solid var(--line);
            display: flex;
            gap: 0.7rem;
            padding: 0.9rem 0.2rem;
        }

        .source-type {
            background: var(--accent-soft);
            border: 1px solid #d9b4a3;
            border-radius: 2px;
            color: var(--accent);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            font-weight: 500;
            padding: 0.25rem 0.5rem;
        }

        .source-id {
            color: var(--muted);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.76rem;
        }

        .source-title {
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 600;
            min-width: 0;
            overflow-wrap: anywhere;
        }

        .graph-shell {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 2px;
            padding: 0.55rem;
        }

        .legend {
            align-items: center;
            color: var(--muted);
            display: flex;
            font-size: 0.84rem;
            gap: 0.5rem;
            margin-top: 0.65rem;
        }

        .legend-swatch {
            background: var(--path-soft);
            border: 2px solid var(--path);
            border-radius: 2px;
            display: inline-block;
            height: 13px;
            width: 13px;
        }

        .backend-status {
            background: var(--accent-soft);
            border: 1px solid #d9b4a3;
            border-radius: 2px;
            color: var(--accent);
            display: inline-block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.68rem;
            margin: 0.35rem 0 0.8rem;
            padding: 0.34rem 0.65rem;
        }

        .backend-status.fallback {
            background: #f1ddd3;
            border-color: #d9b4a3;
            color: #8f3e25;
        }

        .empty-state {
            background: var(--card);
            border: 1px dashed var(--line);
            border-radius: 2px;
            color: var(--muted);
            line-height: 1.6;
            padding: 1.2rem 1.35rem;
        }

        .stCaption, [data-testid="stCaptionContainer"],
        [data-testid="stMarkdownContainer"] p {
            text-wrap: pretty;
        }

        [data-testid="stHorizontalBlock"] {
            align-items: end;
            gap: 0.75rem;
        }

        [data-testid="stButton"] button,
        [data-testid="stTextInput"] input {
            touch-action: manipulation;
            -webkit-tap-highlight-color: rgba(181, 91, 53, 0.18);
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                transition-duration: 0.01ms !important;
            }
        }

        @media (max-width: 767px) {
            .block-container {
                padding: 2.5rem 1rem 3rem;
            }

            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
                gap: 0.35rem;
            }

            [data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                flex: 1 1 auto !important;
            }

            [data-testid="stButton"] button {
                width: 100%;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-kicker">Internal intelligence / connected evidence</div>', unsafe_allow_html=True)
st.title("Company Knowledge Brain")
st.caption("Ask a question. Trace the answer across documents, tickets, and meetings.")

input_column, ask_column = st.columns([5, 1])
with input_column:
    query = st.text_input(
        "Question",
        value="What is the deadline for the customer export feature?",
        placeholder="e.g. What did the product sync say about the ticket?",
    )
with ask_column:
    ask_clicked = st.button("Ask", type="primary")

if query.strip():
    with st.spinner("Following connected evidence…"):
        try:
            result = search_backend.search(query)
        except Exception as error:
            result = None
            st.error(f"Search is temporarily unavailable: {error}")

    status = search_backend.backend_status()
    if status["mode"] == "stub fallback":
        st.markdown(
            '<div class="backend-status fallback">● Stub fallback · real search unavailable</div>',
            unsafe_allow_html=True,
        )
    elif status["mode"] == "real":
        st.markdown(
            '<div class="backend-status">● Real search backend</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="backend-status">● Stub data backend</div>',
            unsafe_allow_html=True,
        )

    if not result or not result.get("answer") or not result.get("sources"):
        st.markdown(
            '<div class="empty-state"><strong>No connected evidence found.</strong><br>'
            'Try a more specific question about the customer export, ticket, meeting, or deadline.</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    st.subheader("Answer")
    st.markdown(f'<div class="answer-card">{result["answer"]}</div>', unsafe_allow_html=True)

    source_types = sorted({source["type"] for source in result["sources"]})
    source_type_label = ", ".join(source_type.replace("_", " ") for source_type in source_types)
    st.caption(f"Evidence spans {len(source_types)} source types: {source_type_label}.")

    st.subheader("Sources")
    for source in result["sources"]:
        source_type = source["type"].replace("_", " ")
        st.markdown(
            f'<div class="source-row"><span class="source-type">{source_type}</span>'
            f'<span class="source-id">{source["id"]}</span>'
            f'<span class="source-title">{source["title"]}</span></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Knowledge graph")
    highlighted = set(result["multi_hop_chain"])
    dot_lines = [
        "digraph G {",
        '  graph [rankdir=LR, bgcolor="#ffffff", pad="0.2"];',
        '  node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, color="#64748b", fillcolor="#f8fafc", fontcolor="#17212b"];',
        '  edge [fontname="Arial", fontsize=9, color="#94a3b8", fontcolor="#64748b"];',
    ]
    for entity in result["entities"]:
        color = "#f1ddd3" if entity["id"] in highlighted else "#f8fafc"
        border = "#b55b35" if entity["id"] in highlighted else "#64748b"
        label = f"{entity['name']}\\n({entity['id']})"
        dot_lines.append(f'  "{entity["id"]}" [label="{label}", fillcolor="{color}", color="{border}"];')
    for relationship in result["relationships"]:
        edge_color = "#b55b35" if relationship["source"] in highlighted and relationship["target"] in highlighted else "#94a3b8"
        penwidth = "2.5" if edge_color == "#b55b35" else "1.0"
        dot_lines.append(
            f'  "{relationship["source"]}" -> "{relationship["target"]}" '
            f'[label="{relationship["relation"]}", color="{edge_color}", penwidth={penwidth}];'
        )
    dot_lines.append("}")
    st.markdown('<div class="graph-shell">', unsafe_allow_html=True)
    graphviz_source = "\n".join(dot_lines)
    try:
        st.graphviz_chart(graphviz_source, width="stretch")
    except TypeError:
        st.graphviz_chart(graphviz_source, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="legend"><span class="legend-swatch"></span>'
        '<strong>Highlighted path</strong> — copper nodes and edges show the ordered '
        'multi-hop reasoning chain.</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "This is not just keyword search: the answer follows linked entities across the "
        "ticket, feature, specification, meeting, and deadline relationships."
    )
else:
    st.markdown(
        '<div class="empty-state"><strong>Ask a question to begin.</strong><br>'
        'The answer will appear with its connected sources and reasoning path.</div>',
        unsafe_allow_html=True,
    )
