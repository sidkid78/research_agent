# start-servers.ps1

Write-Host "Starting Backend Server..." -ForegroundColor Green

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`
    Write-Host 'Setting up backend...' -ForegroundColor Cyan; `
    cd backend; `
    if (Test-Path .\.venv\Scripts\activate.ps1) { `
        .\.venv\Scripts\activate.ps1; `
        Write-Host 'Backend venv activated. Starting uvicorn...' -ForegroundColor Cyan; `
        uvicorn app.main:app --reload; `
    } else { `
        Write-Host 'Backend venv not found. Please run setup.' -ForegroundColor Yellow; `
    } `
    Read-Host 'Backend server window. Press Enter to close...' `
"

Start-Sleep -Seconds 3 # Give backend a moment to start

Write-Host "Starting Frontend Server..." -ForegroundColor Green

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`
    Write-Host 'Setting up frontend...' -ForegroundColor Cyan; `
    cd frontend; `
    if (Test-Path node_modules) { `
        Write-Host 'Starting npm run dev...' -ForegroundColor Cyan; `
        npm run dev; `
    } else { `
        Write-Host 'node_modules not found. Please run npm install.' -ForegroundColor Yellow; `
    } `
    Read-Host 'Frontend server window. Press Enter to close...' `
"

Write-Host "Both server processes launched in separate windows." -ForegroundColor Green 