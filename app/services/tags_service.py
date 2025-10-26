from app.services.transcription_information import all_tags


def get_all_available_tags():
    return all_tags


def get_tags_with_counts():
    tags = get_all_available_tags()
    tag_counts = {tag: 0 for tag in tags}

    # Count occurrences of each tag in the notes
    from app.services.notes_service import load_all_notes
    all_notes = load_all_notes()
    for note in all_notes:
        note_tags = note.get('tags', [])
        for tag in note_tags:
            if tag in tag_counts:
                tag_counts[tag] += 1

    return tag_counts


def get_notes_by_tag(tag):
    from app.services.notes_service import load_all_notes
    all_notes = load_all_notes()
    filtered_notes = [note for note in all_notes if tag in note.get('tags', [])]
    return filtered_notes