.PHONY: build run test clean docker-build docker-run dev

build:
	go build -o bin/main .

run:
	go run .

dev:
	go run .

test:
	go test -v ./...

test-coverage:
	go test -v -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

clean:
	rm -rf bin/
	rm -f coverage.out coverage.html

docker-build:
	docker build -t gin-skeleton .

docker-run:
	docker run -p 8080:8080 gin-skeleton

deps:
	go mod download
	go mod tidy

fmt:
	go fmt ./...

vet:
	go vet ./...

lint:
	golangci-lint run
