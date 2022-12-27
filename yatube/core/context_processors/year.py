from datetime import datetime


def year(request) -> int:
    return {
        'year': datetime.now().year
    }
