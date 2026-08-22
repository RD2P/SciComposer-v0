from graph.workflow_graph import build_workflow_graph
from guard.guard import check_query
import json
from datetime import datetime
import os
import time


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

        print(f"\n[START] Processing query: {query}")
        start_time = time.time()
        
        # Print status for each agent
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Planner agent starting...")
        result = app.invoke({"user_request": query})
        end_time = time.time()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] All agents completed in {end_time - start_time:.2f} seconds")
        
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
        
        # Print formatted workflow information
        workflow = result.get("workflow", {})
        final_workflow = workflow.get("final_workflow", {})
        nodes = final_workflow.get("nodes", [])
        
        if nodes:
            print("\n=== FINAL WORKFLOW ===")
            for i, node in enumerate(nodes, 1):
                print(f"\nStage {i}:")
                print(f"  Tool Name: {node.get('tool', 'Unknown')}")
                print(f"  Reason: {node.get('reason', 'No reason provided')}")
                
                inputs = node.get('inputs', [])
                if inputs:
                    print("  Inputs:")
                    for inp in inputs:
                        print(f"    - {inp}")
                
                outputs = node.get('outputs', [])
                if outputs:
                    print("  Outputs:")
                    for out in outputs:
                        print(f"    - {out}")
        else:
            print("\nNo workflow nodes found.")


if __name__ == "__main__":
    main()