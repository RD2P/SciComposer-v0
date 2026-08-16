from graph.workflow_graph import build_workflow_graph
from guard.guard import check_query


def main() -> None:
    app = build_workflow_graph()

    while True:
        query = input("\n\nEnter your query (or 'exit' to quit): ")

        if query == "":
            continue

        if query.lower() == "exit":
            break

        query_check = check_query(query)

        if query_check == "reject":
            print("Query is not related to a Galaxy scientific workflow.")
            continue

        result = app.invoke({"user_request": query})
        print("RESULT:\n\n", result)


if __name__ == "__main__":
    main()