def get_summary_for_state(state, meeting):
    """
    Returns a tuple summarizing the key parts of the meeting relevant to a state.
    Used to detect changes even if the state remains the same.
    """
    if not meeting:
        return None

    if state == "B":
        return (
            meeting.get("Enter the seminar topic:", "").strip(),
            meeting.get("Enter speaker name here:", "").strip(),
            meeting.get("Choose the DATE when the seminar will be held:", "").strip(),
            meeting.get("Seminar START time:", "").strip(),
        )

    elif state == "C":
        return (
            meeting.get("Enter the seminar topic:", "").strip(),
            meeting.get("Enter speaker name here:", "").strip(),
            meeting.get("Please upload a PHOTO of the speaker here:", "").strip(),
            meeting.get("Enter the abstract of the seminar: (in 150 words)", "").strip(),
        )

    return None
