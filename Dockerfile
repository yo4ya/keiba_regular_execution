# Use an official Python runtime as a parent image
FROM python:3.9.7

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
COPY requirements.txt /app
COPY ./app /app


ENV LANG=ja_JP.UTF-8
ENV PYTHONIOENCODING=utf-8

# Install Chrome and Selenium dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    tzdata \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Set the timezone to JST
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && echo "Asia/Tokyo" > /etc/timezone


# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN wget -O chrome.json https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json && \
    LINUX_STABLE_URL=$(grep -oP '"url":".*?(?=")' chrome.json | grep 'linux64' | head -n 1 | cut -d'"' -f4) && \
    wget -O chrome.zip $LINUX_STABLE_URL && \
    unzip chrome.zip && \
    rm chrome.zip chrome.json

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 環境変数の設定（サービスアカウントキーのパス）
# 本番のときは、コメントアウト
# ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service_account_key.json"

ENV PORT 8080
EXPOSE 8080

# Run gunicorn when the container launches
#CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app", "--reload"]

# Pythonスクリプトを実行するコマンドを設定
ENTRYPOINT ["python", "main.py"]

# コンテナが終了しないようにする(デバッグ用)
# CMD ["tail", "-f", "/dev/null"]