#!/usr/bin/env python3
"""
Deterministic reflection tool — loads tree from JSON, runs session.
"""
import json
import sys
from collections import defaultdict
from typing import Dict, Any, List, Optional

class ReflectionSession:
    def __init__(self, tree_file: str):
        with open(tree_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.current_id = "START"
        self.state = {
            "answers": {},          # node_id -> selected answer text
            "signals": defaultdict(int),
            "axis1": {"internal": 0, "external": 0},
            "axis2": {"contribution": 0, "entitlement": 0},
            "axis3": {"self": 0, "altro": 0}
        }
        self.history = []           # list of node ids visited

    def _interpolate(self, text: str) -> str:
        """Replace {node_id.answer} and {axis.dominant} placeholders."""
        # Replace answer placeholders
        for node_id, answer in self.state["answers"].items():
            text = text.replace(f"{{{node_id}.answer}}", answer)
        # Compute dominants
        axis1_dom = "internal agency" if self.state["axis1"]["internal"] >= self.state["axis1"]["external"] else "external circumstance"
        axis2_dom = "contribution" if self.state["axis2"]["contribution"] >= self.state["axis2"]["entitlement"] else "expectation"
        axis3_dom = "self-focused" if self.state["axis3"]["self"] >= self.state["axis3"]["altro"] else "others-focused"
        text = text.replace("{axis1.dominant}", axis1_dom)
        text = text.replace("{axis2.dominant}", axis2_dom)
        text = text.replace("{axis3.dominant}", axis3_dom)

        # Generate summary_reflection based on dominants
        if "{summary_reflection}" in text:
            if self.state["axis1"]["internal"] >= self.state["axis1"]["external"]:
                ref1 = "You recognized your own agency today."
            else:
                ref1 = "Today felt like things happened *to* you — but even then, you found small choices."
            if self.state["axis2"]["contribution"] >= self.state["axis2"]["entitlement"]:
                ref2 = "You gave more than you took, which is a quiet form of leadership."
            else:
                ref2 = "You noticed a gap between what you expected and what you received. That awareness is the first step toward changing the dynamic."
            if self.state["axis3"]["altro"] >= self.state["axis3"]["self"]:
                ref3 = "Your concern extended beyond yourself — that's where meaning lives."
            else:
                ref3 = "You carried your own weight today. Tomorrow, look for one small way to lighten someone else's."
            summary = f"{ref1} {ref2} {ref3}"
            text = text.replace("{summary_reflection}", summary)
        return text

    def _apply_signal(self, signal_str: str):
        """Parse signal like 'axis1:internal' and update state."""
        if not signal_str:
            return
        if ":" in signal_str:
            axis, pole = signal_str.split(":", 1)
            if axis == "axis1":
                self.state["axis1"][pole] += 1
            elif axis == "axis2":
                self.state["axis2"][pole] += 1
            elif axis == "axis3":
                self.state["axis3"][pole] += 1
            self.state["signals"][signal_str] += 1

    def _display_node(self, node: Dict[str, Any]) -> Optional[str]:
        """Show node text and options; return selected answer or None."""
        text = self._interpolate(node.get("text", ""))
        print("\n" + "─" * 50)
        print(text)
        node_type = node.get("type")
        if node_type in ("question",):
            options = node.get("options", [])
            if not options:
                return None
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            while True:
                try:
                    choice = input("> ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                    else:
                        print(f"Enter 1–{len(options)}")
                except (ValueError, KeyboardInterrupt):
                    if choice.lower() in ('q', 'quit', 'exit'):
                        sys.exit(0)
                    print("Enter a number.")
        return None

    def _next_node_id(self, current: Dict[str, Any], answer: Optional[str] = None) -> str:
        """Determine next node id based on type and branches."""
        ntype = current.get("type")
        # decision node: look up branch based on previous answer
        if ntype == "decision":
            # answer is the selected option from the parent question
            branches = current.get("branches", {})
            # Try exact match first, then maybe prefix? We'll assume exact.
            return branches.get(answer, None)
        # bridge, reflection, start, etc. have target
        if "target" in current and current["target"]:
            return current["target"]
        # fallback: if no target, we can't continue
        return None

    def run(self):
        """Main loop."""
        while self.current_id:
            node = self.nodes.get(self.current_id)
            if not node:
                print(f"Error: node '{self.current_id}' not found.")
                break
            self.history.append(self.current_id)
            ntype = node.get("type")

            # Apply signals
            for sig in node.get("signal", []):
                self._apply_signal(sig)

            answer = None
            if ntype == "end":
                self._display_node(node)
                break

            # For decision nodes, we need the answer from the immediate previous question
            if ntype == "decision":
                # The parent should be the last question node visited
                parent_id = self.history[-2] if len(self.history) >= 2 else None
                if parent_id:
                    answer = self.state["answers"].get(parent_id)
                if answer is None:
                    print("Error: no answer available for decision.")
                    break
                next_id = self._next_node_id(node, answer)
                self.current_id = next_id
                continue

            # Interactive nodes (question)
            answer = self._display_node(node)
            if ntype == "question":
                self.state["answers"][self.current_id] = answer
                next_id = self._next_node_id(node, answer)
                self.current_id = next_id
                continue

            # Non-interactive nodes (start, reflection, bridge, summary)
            if ntype in ("start", "reflection", "bridge", "summary"):
                self._display_node(node)
                input("Press Enter to continue...")
                next_id = self._next_node_id(node)
                self.current_id = next_id
                continue

            # Fallback
            next_id = self._next_node_id(node, answer)
            self.current_id = next_id

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reflection_agent.py <tree.json>")
        sys.exit(1)
    session = ReflectionSession(sys.argv[1])
    session.run()
    