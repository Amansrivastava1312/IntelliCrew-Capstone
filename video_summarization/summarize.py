from typing import TypedDict
from langgraph.graph import StateGraph, END

from transformers import pipeline
import re

from video_summarization.db import save_video_summary_log


# load the summarizer ONCE (light model, CPU friendly)
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


# shared state passed between nodes
class SummaryState(TypedDict):
    source: str                 # YouTube URL or local file path (inside videos/)
    is_url: bool                # True if source is a link
    transcript: str             # extracted text
    summary: str                # final summary
    status: str                 # done / no_transcript
    session_id: str             # Manager or HR ID supplied by app.py


# small helpers (reused inside nodes)
def get_youtube_id(url: str):
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def whisper_transcribe(file_path: str) -> str:
    import whisper
    model = whisper.load_model("base")   # use "tiny" if VM is really weak
    result = model.transcribe(file_path)
    return result["text"]


# 1. detect source type (url vs local file) — branch point
def node_detect(state):
    src = state["source"].strip()
    state["source"] = src
    state["is_url"] = src.startswith("http")
    return state


def route_after_detect(state):
    return "youtube" if state["is_url"] else "whisper"


# 2. youtube captions (fast, no compute) — branch point
def node_youtube(state):
    vid = get_youtube_id(state["source"])
    if not vid:
        state["transcript"] = ""
        return state
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        try:
            # NEW API (v1.0+): instance + .fetch()
            api = YouTubeTranscriptApi()
            fetched = api.fetch(vid)
            state["transcript"] = " ".join(s.text for s in fetched)
        except AttributeError:
            # OLD API fallback: static .get_transcript()
            parts = YouTubeTranscriptApi.get_transcript(vid)
            state["transcript"] = " ".join(p["text"] for p in parts)
    except Exception as e:
        print("No captions available:", e)
        state["transcript"] = ""
    return state


def route_after_youtube(state):
    # captions found -> summarize ; else fall back to whisper (needs audio)
    return "summarize" if state["transcript"].strip() else "whisper"


# 3. whisper transcription (local files, or url with no captions)
def node_whisper(state):
    state["transcript"] = whisper_transcribe(state["source"])
    return state


# 4. summarize in chunks (length scales with video)
def node_summarize(state):
    text = (state.get("transcript") or "").strip()
    if not text:
        state["summary"] = "No text found to summarize."
        state["status"] = "no_transcript"
        return state

    # split into ~3000-char chunks so we don't exceed model limits
    chunks = [text[i:i + 3000] for i in range(0, len(text), 3000)]

    partial = []
    for ch in chunks:
        s = summarizer(ch, max_length=250, min_length=100, do_sample=False)
        partial.append(s[0]["summary_text"])

    # few chunks -> just join, already detailed
    if len(partial) <= 3:
        state["summary"] = "\n\n".join(partial)
        state["status"] = "done"
        return state

    # long video -> re-summarize in small groups so output stays detailed
    grouped = []
    group_size = 3
    for i in range(0, len(partial), group_size):
        block = " ".join(partial[i:i + group_size])
        s = summarizer(block, max_length=250, min_length=100, do_sample=False)
        grouped.append(s[0]["summary_text"])

    state["summary"] = "\n\n".join(grouped)
    state["status"] = "done"
    return state


# 5. call the database execution helper after summarization
def node_save_to_db(state):
    save_video_summary_log(
        file_path=state["source"],
        summary=state["summary"],
        session_id=state["session_id"],
    )
    return state


def build_graph():
    g = StateGraph(SummaryState)
    g.add_node("detect", node_detect)
    g.add_node("youtube", node_youtube)
    g.add_node("whisper", node_whisper)
    g.add_node("summarize", node_summarize)
    g.add_node("save_to_db", node_save_to_db)

    g.set_entry_point("detect")
    g.add_conditional_edges("detect", route_after_detect,
                            {"youtube": "youtube", "whisper": "whisper"})
    g.add_conditional_edges("youtube", route_after_youtube,
                            {"summarize": "summarize", "whisper": "whisper"})
    g.add_edge("whisper", "summarize")
    g.add_edge("summarize", "save_to_db")
    g.add_edge("save_to_db", END)
    return g.compile()


summarizer_agent = build_graph()
