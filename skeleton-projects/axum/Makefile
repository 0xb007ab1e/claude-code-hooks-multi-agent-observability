.PHONY: build run test clean docker-build docker-run dev

build:
	cargo build --release

run:
	cargo run

dev:
	cargo watch -x run

test:
	cargo test

test-coverage:
	cargo tarpaulin --out html

clean:
	cargo clean

docker-build:
	docker build -t axum-skeleton .

docker-run:
	docker run -p 3000:3000 axum-skeleton

deps:
	cargo update

fmt:
	cargo fmt

clippy:
	cargo clippy -- -D warnings

check:
	cargo check
