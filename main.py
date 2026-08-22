from graph.workflow_graph import build_workflow_graph
from guard.guard import check_query
import json
from datetime import datetime
import os


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
        
        # Create filename with date/time and first 3 words of query
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        words = query.split()
        first_three_words = "_".join(words[:3]) if len(words) >= 3 else "_".join(words)
        # Sanitize filename by removing invalid characters
        first_three_words = "".join(c for c in first_three_words if c.isalnum() or c == '_')
        filename = f"{timestamp}_{first_three_words}.json"
        
        # Write result to outputs directory
        output_path = os.path.join("outputs", filename)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Result saved to {output_path}")


if __name__ == "__main__":
    main()