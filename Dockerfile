FROM ubuntu:latest
FROM python:3.11.5

RUN apt-get update
RUN pip install "openai==1.3.5"
RUN pip install "openapi==1.1.0"
RUN pip install "chainlit==0.7.604"

ENV ASSISTANT_ID= YOUR_ASSISTANT_ID
ENV OPENAI_API_KEY= YOUR_OPENAI_API_KEY

COPY assistant.py .
RUN mkdir .chainlit
COPY .chainlit/config.toml .chainlit/
RUN mkdir public
COPY public/test.css public/
COPY chainlit.md .

CMD ["chainlit", "run", "assistant.py"]
