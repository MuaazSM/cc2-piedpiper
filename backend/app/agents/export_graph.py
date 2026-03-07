"""
Standalone script to export the LangGraph flow diagram.

Run from the repo root:
    python -m backend.app.agents.export_graph

Outputs:
    data/langgraph_flow.mermaid  — Mermaid diagram source
    data/langgraph_flow.png      — PNG image (if mermaid deps available)

The .mermaid file can be:
- Pasted into GitHub README inside a ```mermaid code block
- Opened at https://mermaid.live for visual editing
- Embedded in Google Slides / PowerPoint as an image (use the PNG)
- Converted to PNG via CLI: npx @mermaid-js/mermaid-cli -i langgraph_flow.mermaid -o langgraph_flow.png
"""

from backend.app.agents.langgraph_pipeline import export_graph_diagram


def main():
    print("=" * 60)
    print("Lorri — LangGraph Flow Diagram Export")
    print("=" * 60)

    result = export_graph_diagram(
        output_dir="data",
        filename="langgraph_flow",
    )

    print("\n--- Mermaid Source ---")
    print(result["mermaid_string"])
    print("--- End ---\n")

    if result["png_path"]:
        print(f"PNG saved: {result['png_path']}")
    else:
        print("PNG not generated. To create one manually:")
        print("  Option 1: Paste the .mermaid file into https://mermaid.live")
        print("  Option 2: npx @mermaid-js/mermaid-cli -i data/langgraph_flow.mermaid -o data/langgraph_flow.png")

    print(f"\nMermaid file: {result['mermaid_path']}")
    print("\nTo embed in README, add this to your README.md:")
    print("  ```mermaid")
    print("  <paste contents of data/langgraph_flow.mermaid>")
    print("  ```")


if __name__ == "__main__":
    main()