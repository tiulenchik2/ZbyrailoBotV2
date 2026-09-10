from datetime import date

def validate_birthdate(text: str) -> date | None:
    '''
    Replaces user's input into date object
    If fails, return None
    '''
    try:
        parts = text.strip().split('.')
        if len(parts) != 2:
            return None
        day, month = int(parts[0]), int(parts[1])
        return date(2000, month, day)
    except (ValueError, IndexError):
        return None
