# Python Virtual Environment Rules

## Mandatory Rules
- Always activate `.venv\Scripts\activate` before running Python scripts on Windows.
- Use `.\.venv\Scripts\python.exe <script>` to execute scripts.
- Never use global Python for this project.

## Reason
Prevents dependency conflicts like "missing pulp".
