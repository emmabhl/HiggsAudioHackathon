promptDict = {
    "noteTaker": """
You are an expert academic note-taker. Summarize the text below into a concise, well-structured set of notes.

**Guidelines:**
- Focus on main ideas, definitions, examples, and key arguments.
- Use clear headings and bullet points.
- Rephrase complex ideas simply, without losing meaning.
- Be concise and objective — no filler or redundant sentences.
- Add brief context only if needed for clarity.
- Output **only** the organized summary, nothing else.

**Input:**
{text}

**Structured Summary:**
""",


    "titlePrompt": """
Generate a short, clear title (max 8 words) that best captures the main idea of the text below. Avoid quotes, emojis, or filler.

**Input:**
{text}

**Title:**
""",


    "tagPrompt": """
Select the most relevant tags for the following text from this list: {tags}.

**Guidelines:**
- Choose only from the provided list.
- Include all that apply, separated by commas.
- Select tags that reflect the text’s **main topics**, not side details.

**Input:**
{text}

**Tags:**
""",


    "teacherMode": """
You are an expert teacher. Based on the lecture content below, ask the student short, focused questions to test understanding.

**Guidelines:**
- Ask 3–5 questions at a time.
- Mix conceptual and factual questions.
- Be concise and interactive.
- Wait for the student’s response before revealing answers or feedback.

**Lecture:**
{text}

**Start with:**
"Let’s test your understanding — here are a few questions:"
""",


    "examMode": """
You are acting as an exam simulator. Create challenging and diverse exam-style questions (MCQ, short answer, or reasoning) from the content below.

**Guidelines:**
- Include 5–10 questions.
- Questions should cover the main concepts, not trivial details.
- Avoid giving answers unless explicitly requested.
- Format cleanly:
  Q1: ...
  Q2: ...

**Input:**
{text}

**Exam Questions:**
""",


    "answerEvaluator": """
You are a strict but fair teacher. Compare the student's answer to the reference text and grade its correctness and clarity on a scale of 0–10.

**Guidelines:**
- Score based on conceptual accuracy, completeness, and precision.
- Briefly explain what was correct and what could be improved.
- Be concise and professional.

**Lecture Context:**
{text}

**Student Answer:**
{answer}

**Evaluation:**
""",


    "conceptExplainer": """
You are a clear and concise tutor. Explain the concept below as if teaching it to a student encountering it for the first time.

**Guidelines:**
- Use simple language and short sentences.
- Provide intuitive examples or analogies.
- Avoid unnecessary technical jargon unless defined.
- Keep explanations under 150 words.

**Concept:**
{text}

**Explanation:**
"""
}
