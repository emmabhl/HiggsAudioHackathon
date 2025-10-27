import markdown
from app.services.text_gen_service import call_qwen_endpoint
from app.services.notes_service import load_all_notes
from app.services.promptLibrary import promptDict


def infer_mode(query: str) -> str:
    """Infer which prompt mode to use based on the student's query."""
    q = query.lower()

    if any(k in q for k in ["teach", "quiz", "question me", "test my knowledge", "teacher mode", "test me"]):
        return "teacherMode"
    elif any(k in q for k in ["exam", "mock exam", "practice test", "challenge me"]):
        return "examMode"
    elif any(k in q for k in ["evaluate", "grade", "score", "check my answer"]):
        return "answerEvaluator"
    elif any(k in q for k in ["explain", "clarify", "help me understand", "what is", "define"]):
        return "conceptExplainer"
    else:
        return None


def build_prompt(context: str, query: str, last_question: str="") -> str:
        """Construct the full generation prompt dynamically based on inferred mode."""
        mode = infer_mode(query)
        template = promptDict.get(mode, None)

        prompt = f"""
            You are an AI teaching assistant helping students learn efficiently from lecture materials.
            Your answers must be accurate, concise, and directly useful for learning. Generate responses
            with basic punctuation only (no special formatting or mathematical symbols), be brief!

            # Context
            {context.strip()}
            
            # Last Assistant Response
            {last_question.strip() if last_question else "N/A"}

            # Instruction
            {template.strip().format(text=context, query=query) if template else ""}

            # Student Query
            {query.strip()}

            # Answer:
            """
        return prompt, mode


def get_rag_summary(query, matching_notes, markdown=True, last_question=""):
    """
    Perform a retrieval-augmented generation for the query using the saved notes as context.

    Args:
        query (str): The search query.
        matching_notes (List[dict]): List of relevant notes to provide context.

    Returns:
        Tuple[str, list]: Tuple containing the generated summary and the list of relevant notes.
    """

    # Step 1: Prepare context from matching notes
    if len(matching_notes) == 0:
        prompt = build_prompt("", query, last_question)[0]
    else:
        context = ""
        for note in matching_notes:
            transcription = note.get('transcription', '')
            context += f"Note ID: {note.get('id')}\nNote Date: {note.get('datetime')}\n{transcription}\n\n"

        # Step 2: Format the prompt using the template
        prompt = build_prompt(context, query, last_question)[0]

    # Step 3: Call Ollama to get the answer
    try:
        summary = call_qwen_endpoint(prompt)
        #ollama.generate(model="llama3.2:3b", prompt=prompt)  # Adjust model name if necessary
        #summary = response.get("response", "")
    except Exception as e:
        summary = f"An error occurred while generating the summary: {str(e)}"

    # Step 4: Return the summary and relevant notes
    summary = summary.replace("\n", "\n\n").replace("\n\n\n\n", "\n\n")

    if markdown:
        return markdown.markdown(summary)
    return summary