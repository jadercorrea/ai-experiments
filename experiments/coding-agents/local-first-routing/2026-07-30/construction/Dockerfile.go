# syntax=docker/dockerfile:1.19
FROM golang:1.25-bookworm@sha256:ea341baa9bd5ba6784f6d7161ace70544349a6242d54d34a0fbfd2c4d51c9d58

ENV CGO_ENABLED=1 \
    GOCACHE=/home/evaluator/.cache/go-build \
    GOTOOLCHAIN=local

RUN useradd --create-home --uid 10001 evaluator

WORKDIR /workspace

COPY go.* ./
RUN go mod download

COPY --chown=evaluator:evaluator . .
RUN chown -R evaluator:evaluator /workspace

USER evaluator
