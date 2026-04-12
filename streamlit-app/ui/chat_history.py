"""
Chat History UI & Persistence

Handles creating, loading, and rendering persistent chat sessions.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

def create_new_session(db_manager, user_id: str, config_name: str = "standard") -> str:
    """
    Create a new chat session in the database.

    Returns the new chat_session_id.
    """
    from context.db_models import ChatSessionRecord
    session_record = ChatSessionRecord(
        user_id=user_id,
        title="New Conversation",
        config_name=config_name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    with db_manager.get_session() as session:
        session.add(session_record)
        session.flush()
        session_id = session_record.chat_session_id
    return session_id


def load_session_messages(db_manager, chat_session_id: str) -> List[Dict[str, Any]]:
    """
    Load all messages for a session from the database.

    Returns a list of dicts compatible with st.session_state.messages format.
    """
    from context.db_models import ChatMessageRecord
    with db_manager.get_session() as session:
        records = (
            session.query(ChatMessageRecord)
            .filter_by(chat_session_id=chat_session_id)
            .order_by(ChatMessageRecord.sequence_number)
            .all()
        )
        return [
            {
                "role": r.role,
                "content": r.content,
                "steps": r.steps_json or [],
            }
            for r in records
        ]


def save_message(
    db_manager,
    chat_session_id: str,
    role: str,
    content: str,
    steps: Optional[List] = None,
) -> None:
    """
    Persist a chat message and update session's updated_at timestamp.
    """
    from context.db_models import ChatMessageRecord, ChatSessionRecord
    try:
        with db_manager.get_session() as session:
            # Get next sequence number
            last = (
                session.query(ChatMessageRecord)
                .filter_by(chat_session_id=chat_session_id)
                .order_by(ChatMessageRecord.sequence_number.desc())
                .first()
            )
            seq = (last.sequence_number + 1) if last else 0

            # Serialize steps (strip non-serializable objects)
            serialized_steps = None
            if steps:
                try:
                    serialized_steps = [
                        {
                            "tool": getattr(action, "tool", str(action)),
                            "tool_input": getattr(action, "tool_input", ""),
                            "observation": obs,
                        }
                        for action, obs in steps
                    ]
                except Exception:
                    serialized_steps = None

            msg = ChatMessageRecord(
                chat_session_id=chat_session_id,
                role=role,
                content=content,
                steps_json=serialized_steps,
                timestamp=datetime.now(),
                sequence_number=seq,
            )
            session.add(msg)

            # Update session's updated_at and auto-title from first user message
            chat_session = session.query(ChatSessionRecord).filter_by(
                chat_session_id=chat_session_id
            ).first()
            if chat_session:
                chat_session.updated_at = datetime.now()
                if (
                    role == "user"
                    and chat_session.title == "New Conversation"
                ):
                    chat_session.title = content[:60].strip()
    except Exception as e:
        print(f"[chat_history] save_message error: {e}")


def list_user_sessions(
    db_manager,
    user_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Return recent chat sessions for a user, newest first.
    """
    from context.db_models import ChatSessionRecord
    try:
        with db_manager.get_session() as session:
            records = (
                session.query(ChatSessionRecord)
                .filter_by(user_id=user_id, is_archived=False)
                .order_by(ChatSessionRecord.updated_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "chat_session_id": r.chat_session_id,
                    "title": r.title,
                    "updated_at": r.updated_at,
                    "config_name": r.config_name,
                }
                for r in records
            ]
    except Exception as e:
        print(f"[chat_history] list_user_sessions error: {e}")
        return []


def delete_session(db_manager, chat_session_id: str) -> None:
    """Archive (soft-delete) a session."""
    from context.db_models import ChatSessionRecord
    try:
        with db_manager.get_session() as session:
            record = session.query(ChatSessionRecord).filter_by(
                chat_session_id=chat_session_id
            ).first()
            if record:
                record.is_archived = True
    except Exception as e:
        print(f"[chat_history] delete_session error: {e}")


# ---------------------------------------------------------------------------
# Sidebar rendering
# ---------------------------------------------------------------------------

def render_sidebar_history(db_manager, user_id: str) -> None:
    """
    Render the chat history list in the sidebar.

    Clicking a session loads it; clicking New Chat starts fresh.
    """
    # New Chat button
    if st.button("＋  New Conversation", use_container_width=True, type="primary"):
        _start_new_chat(db_manager, user_id)
        st.rerun()

    st.markdown(
        "<p style='font-size:0.75rem;color:#64748b;margin:0.8rem 0 0.3rem'>Recent Conversations</p>",
        unsafe_allow_html=True,
    )

    sessions = list_user_sessions(db_manager, user_id)

    if not sessions:
        st.markdown(
            "<p style='font-size:0.8rem;color:#475569;padding:0.4rem 0'>No conversations yet.</p>",
            unsafe_allow_html=True,
        )
        return

    current_id = st.session_state.get("current_chat_session_id")

    for s in sessions:
        sid = s["chat_session_id"]
        title = s["title"] or "Untitled"
        is_active = sid == current_id

        # Truncate long titles
        display_title = (title[:38] + "…") if len(title) > 40 else title

        # Style the active session differently
        btn_type = "secondary" if is_active else "tertiary" if hasattr(st, "button") else "secondary"

        col_btn, col_del = st.columns([5, 1], vertical_alignment="center")
        with col_btn:
            label = f"{'▶ ' if is_active else ''}{display_title}"
            if st.button(label, key=f"session_{sid}", use_container_width=True):
                if sid != current_id:
                    _load_existing_chat(db_manager, sid)
                    st.rerun()
        with col_del:
            if st.button("✕", key=f"del_{sid}", help="Remove conversation", use_container_width=True):
                delete_session(db_manager, sid)
                if sid == current_id:
                    _start_new_chat(db_manager, user_id)
                st.rerun()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start_new_chat(db_manager, user_id: str) -> None:
    """Initialize session state for a brand-new chat."""
    config_name = st.session_state.get("selected_config", "standard")
    new_id = create_new_session(db_manager, user_id, config_name)
    st.session_state["current_chat_session_id"] = new_id
    st.session_state["messages"] = []
    st.session_state.pop("generated_report", None)
    st.session_state.pop("identified_drug", None)
    st.session_state.pop("drug_msg_count", None)
    st.session_state.pop("report_dev_log", None)


def _load_existing_chat(db_manager, chat_session_id: str) -> None:
    """Load a past session into session state."""
    messages = load_session_messages(db_manager, chat_session_id)
    st.session_state["current_chat_session_id"] = chat_session_id
    st.session_state["messages"] = messages
    st.session_state.pop("generated_report", None)
    st.session_state.pop("identified_drug", None)
    st.session_state.pop("drug_msg_count", None)
    st.session_state.pop("report_dev_log", None)


def ensure_active_session(db_manager, user_id: str) -> str:
    """
    Ensure there is an active chat session in session state.
    Creates one if not yet set. Returns the session ID.
    """
    if "current_chat_session_id" not in st.session_state:
        _start_new_chat(db_manager, user_id)
    return st.session_state["current_chat_session_id"]
