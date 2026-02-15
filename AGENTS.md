# AGENTS.md



## Chatting

- I might end the prompts with commands. It will start with '\', followed by  all the commands I want for you to consider in your response. These are the commands:
\c - an extremely concise response.
\s{number} - a response with up to {number} sentences.


## General

- every time you do something, i check it and find a bug, send it back to you, you find the issue and solve it - i want you to go to the lessons learned file and add a sentence or two of how you will next time avoid this specific or general issue and not having that bug in the first place. add it to the end of the file. add one extra new line every time you update that file.






## Workflow
- Do not change unrelated code.
- Preserve existing behavior unless the task explicitly requires behavioral changes.

## Dependency and Security Rules
- When adding a dependency, choose actively maintained packages and keep usage minimal.
- Never hardcode secrets or tokens.
- Use environment variables for credentials and sensitive config.