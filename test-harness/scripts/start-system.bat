@echo off
REM Windows batch file to start system with dynamic ports

REM Read port assignment from JSON file
set CONFIG_FILE=config\port_assignments.json

REM Read base port from JSON (requires jq for Windows or alternative method)
for /f "tokens=*" %%i in ('jq -r .base_port %CONFIG_FILE%') do set BASE_PORT=%%i

REM Fallback to default if not set
if "%BASE_PORT%"=="" set BASE_PORT=8090
if "%BASE_PORT%"=="null" set BASE_PORT=8090

REM Calculate client port
set /a CLIENT_PORT=%BASE_PORT%+83

REM Export dynamic ports
set BASE_PORT=%BASE_PORT%
set CLIENT_PORT=%CLIENT_PORT%

REM Read other ports from JSON
for /f "tokens=*" %%i in ('jq -r .assignments."http-server".port %CONFIG_FILE%') do set HTTP_SERVER_PORT=%%i
for /f "tokens=*" %%i in ('jq -r .assignments."postgres".port %CONFIG_FILE%') do set POSTGRES_PORT=%%i
for /f "tokens=*" %%i in ('jq -r .assignments."mongo".port %CONFIG_FILE%') do set MONGO_PORT=%%i

REM Print assigned ports
echo BASE_PORT: %BASE_PORT%
echo CLIENT_PORT: %CLIENT_PORT%
echo HTTP_SERVER_PORT: %HTTP_SERVER_PORT%

echo Launching the services...
REM Add the command to start your application here, for example:
REM bun run app.js
REM npm start
