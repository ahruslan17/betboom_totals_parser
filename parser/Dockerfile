FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install -r requirements.txt
RUN playwright install --with-deps

CMD ["/bin/bash"]
