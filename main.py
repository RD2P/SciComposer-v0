from graph.workflow_graph import build_workflow_graph

def main() -> None:
    app = build_workflow_graph()

    while True:
        query = input("\n\nEnter your query (or 'exit' to quit): ")
        
        if query.lower() == 'exit':
            break

        result = app.invoke({"user_request": query})
        print(result)        


if __name__ == "__main__":
    main()