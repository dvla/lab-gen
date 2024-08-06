ARG VARIANT=slim-bookworm
ARG VERSION=3.11
FROM python:${VERSION}-${VARIANT} AS builder

# Install poetry
RUN python -m pip install poetry
# Configuring poetry
RUN poetry config virtualenvs.create false

RUN groupadd -g 10001 genapp && \
    useradd -u 10000 -g genapp genapp
# && chown -R genapp:genapp /app
USER genapp:genapp
WORKDIR /home/genapp

FROM builder
COPY --chown=genapp:genapp . .
RUN poetry install --only main
ENV PATH="/home/genapp/.local/bin:${PATH}"
# Start the app
EXPOSE 8000:8000
CMD poetry run python -m lab_gen
