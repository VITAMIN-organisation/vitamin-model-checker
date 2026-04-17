.PHONY: build run test clean

IMAGE_NAME=model-checker

build:
	docker build -t $(IMAGE_NAME) -f Dockerfile ..

run:
	docker run --rm $(IMAGE_NAME)

test:
	docker run --rm $(IMAGE_NAME) pytest tests/unit

clean:
	docker rmi $(IMAGE_NAME) || true
