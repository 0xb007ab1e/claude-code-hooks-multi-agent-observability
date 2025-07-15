.PHONY: install dev test build clean docker-build docker-run

install:
	npm install

dev:
	npm run dev

test:
	npm test

build:
	npm run build

clean:
	rm -rf node_modules

docker-build:
	docker build -t express-skeleton .

docker-run:
	docker run -p 3000:3000 express-skeleton

lint:
	npm run lint

lint-fix:
	npm run lint:fix
