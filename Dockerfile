FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GIT_AUTHOR_NAME="QA Guru TMS Automator" \
    GIT_AUTHOR_EMAIL="automator@local" \
    GIT_COMMITTER_NAME="QA Guru TMS Automator" \
    GIT_COMMITTER_EMAIL="automator@local"

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
         -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
         > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY templates ./templates

RUN python -m pip install --no-cache-dir .

RUN mkdir -p /app/data /app/projects

CMD ["automator"]
