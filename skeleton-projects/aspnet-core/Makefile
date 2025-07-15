.PHONY: build run test clean docker-build docker-run dev restore

restore:
	dotnet restore

build:
	dotnet build

run:
	dotnet run

dev:
	dotnet watch run

test:
	dotnet test

clean:
	dotnet clean
	rm -rf bin/ obj/

docker-build:
	docker build -t aspnet-core-skeleton .

docker-run:
	docker run -p 5000:80 aspnet-core-skeleton

publish:
	dotnet publish -c Release -o ./publish

format:
	dotnet format
