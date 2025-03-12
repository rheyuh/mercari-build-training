FROM alpine


RUN apk add python3
RUN apk add py3-pip
RUN mkdir src

COPY . src

RUN cd src
RUN addgroup -S mercari && adduser -S trainee -G mercari
RUN chown -R trainee:mercari src/db
RUN python3 -m venv /app/venv

# Set path to use the virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Now pip commands will use the virtual environment
# RUN pip install --upgrade pip
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r src/requirements.txt

USER trainee

# CMD ["python", "-V"]
# CMD ["ls", "src"]
WORKDIR src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload", "--port", "9000"]