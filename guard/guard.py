from .rules import check_rules


def check_query(query: str) -> str:
    return check_rules(query)