.PHONY: build run test clean

IMAGE_NAME=vitamin-model-checker

build:
	docker build -t $(IMAGE_NAME) -f Dockerfile ..

run:
	docker run --rm $(IMAGE_NAME)

test:
	docker run --rm $(IMAGE_NAME) pytest model_checker/tests/unit

clean:
	docker rmi $(IMAGE_NAME) || true
