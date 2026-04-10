# i3X API Client

TODO - for right now this is a single file that's a test client for streaming mode (server sent events). We will change this into a full client.

## Project Structure

## Setting Up the Virtual Environment

### Prerequisites
- Python 3.7 or higher
- pip

### Setup Instructions

1. **Create a virtual environment**:

Windows:
```powershell
# Navigate to the project directory
cd c:\Users\<user>\i3x

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate
```

Linux/Mac
```bash
# Navigate to the project directory
cd ~/i3x

# Create a virtual environemnt
python -m venv venv

# Activate the virtual environment
chmod +x ./venv/bin/activate
./venv/bin/activate
```

2. **Install dependencies**:

```
pip install -r requirements.txt
```

3. **Run the client**:

```
python test_client.py
```

