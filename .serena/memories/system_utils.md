# System Utilities Reference (Darwin/macOS)

## File System Commands
```bash
# List files
ls -la              # List all files with details
ls -lh              # Human-readable file sizes
ls *.py             # List Python files

# Navigate directories
pwd                 # Print working directory
cd /path/to/dir     # Change directory
cd ..               # Go up one level
cd ~                # Go to home directory

# File operations
cp source dest      # Copy file
mv old new          # Move/rename file
rm file             # Remove file (use with caution)
mkdir dirname       # Create directory
touch filename      # Create empty file

# File content
cat file            # Display file content
head -n 10 file     # First 10 lines
tail -n 10 file     # Last 10 lines
less file           # Page through file
```

## Search Commands
```bash
# Find files
find . -name "*.py"                    # Find Python files
find . -type f -name "test_*"          # Find test files
find . -type d -name "__pycache__"     # Find directories

# Search in files (use ripgrep if available)
grep -r "pattern" .                    # Recursive search
grep -n "pattern" file                 # Show line numbers
grep -i "pattern" file                 # Case insensitive

# ripgrep (faster alternative)
rg "pattern"                            # Search recursively
rg -t py "pattern"                      # Search only Python files
```

## Process Management
```bash
# View processes
ps aux              # All processes
ps aux | grep python # Python processes
top                 # Interactive process viewer

# Kill processes
kill PID            # Kill by process ID
killall processname # Kill by name
```

## Environment
```bash
# Environment variables
echo $PATH          # View PATH
export VAR=value    # Set variable
env                 # List all variables

# Python environment
which python        # Python location
python --version    # Python version
pip list            # Installed packages
```

## Git Essentials
```bash
# Status and info
git status          # Working tree status
git log --oneline   # Commit history
git branch          # List branches
git diff            # Unstaged changes

# Basic workflow
git add .           # Stage all changes
git commit -m "msg" # Commit with message
git push origin branch # Push to remote
git pull            # Update from remote

# Branches
git checkout -b new-branch  # Create and switch
git checkout branch         # Switch branch
git merge branch           # Merge branch
```

## Network/API Testing
```bash
# Test endpoints
curl http://localhost:8501     # Test Streamlit
curl -X GET url                # GET request
curl -X POST url -d '{}'       # POST with data

# Port checking
lsof -i :8501                  # What's using port 8501
netstat -an | grep 8501        # Port status
```

## macOS Specific
```bash
# Open in Finder
open .              # Open current directory
open file.txt       # Open with default app

# Clipboard
pbcopy < file       # Copy file to clipboard
pbpaste > file      # Paste clipboard to file
echo "text" | pbcopy # Copy text to clipboard

# System info
sw_vers             # macOS version
system_profiler SPSoftwareDataType # Detailed system info
```

## Development Shortcuts
```bash
# Python virtual environments (if not using uv)
python -m venv venv             # Create venv
source venv/bin/activate        # Activate (macOS)
deactivate                      # Deactivate

# Quick Python tests
python -c "import pandas; print(pandas.__version__)"  # Check package
python -m pytest --version      # Check pytest
```

## Important Notes
- macOS uses BSD versions of some commands (slightly different from Linux)
- Case-insensitive filesystem by default (be careful with filenames)
- Use `brew` for installing additional tools if needed
- `.DS_Store` files are created automatically (already in .gitignore)
