import markdown
import ollama

from app.services.notes_service import load_all_notes


def get_rag_summary(query, matching_notes, markdown=True):
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
        prompt = f"""
        You are an assistant who provides answers to the user's questions. Make the response quick and concise please, just a short summary.

        # Question
        {query}

        # Answer:
        """
    else:
        context = ""
        for note in matching_notes:
            transcription = note.get('transcription', '')
            context += f"Note ID: {note.get('id')}\nNote Date: {note.get('datetime')}\n{transcription}\n\n"

        # Step 2: Format the prompt using the template
        prompt = f"""
        You are an assistant who uses the provided context to answer the question accurately. 
        Use the information from the notes to generate a detailed yet concise response.

        # Context
        {context}

        # Question
        {query}

        # Answer:
        """

    # Step 3: Call Ollama to get the answer
    try:
        response = ollama.generate(model="llama3.2:3b", prompt=prompt)  # Adjust model name if necessary
        summary = response.get("response", "")
    except Exception as e:
        summary = f"An error occurred while generating the summary: {str(e)}"

    # Step 4: Return the summary and relevant notes
    summary = summary.replace("\n", "\n\n").replace("\n\n\n\n", "\n\n")

    if markdown:
        return markdown.markdown(summary)
    return summary