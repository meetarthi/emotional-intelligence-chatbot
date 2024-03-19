FROM ubuntu:latest
FROM python:3.11.5

RUN apt-get update
RUN pip install "openai==1.3.5"
RUN pip install "openapi==1.1.0"
RUN pip install "chainlit==0.7.604"

ENV ASSISTANT_ID=asst_NkiKj37mUnVyEboJwwAGiDwp
ENV OPENAI_API_KEY=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

COPY assistant.py .
RUN mkdir .chainlit
COPY .chainlit/config.toml .chainlit/
RUN mkdir public
COPY public/test.css public/
COPY chainlit.md .

CMD ["chainlit", "run", "assistant.py"]