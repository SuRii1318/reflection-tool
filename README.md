# Reflection Tool

A deterministic, end-of-day reflection tool that guides employees through a structured conversation based on established psychological frameworks.

## What it Does

This tool walks you through a series of questions to help you reflect on your day, focusing on three key psychological axes:
1.  **Locus of Control**: How much agency did you feel you had over the day's events?
2.  **Orientation**: Were you more focused on what you gave or what you received?
3.  **Radius**: Was your concern primarily for yourself or for others?

## How to Run

1.  Ensure you have Python 3 installed.
2.  Clone this repository: `git clone [your-repo-url-will-go-here]`
3.  Navigate to the project directory: `cd reflection-tool`
4.  Run the script: `python reflection_agent.py reflection_tree.json`

## File Structure

*   `reflection_agent.py`: The Python script that runs the reflection session.
*   `reflection_tree.json`: The data file containing the entire decision tree of questions, options, and reflections.