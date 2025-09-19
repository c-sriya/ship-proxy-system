# Ship Proxy System 
This project implements a single-TCP connection proxy system for a cruise ship scenario. It includes: - 
- **Client (Ship Proxy)**: Handles HTTP/S requests from browsers or curl, queues them, and sends them sequentially to the offshore proxy server. 
- **Server (Offshore Proxy)**: Receives requests from the ship proxy over a single TCP connection, forwards them to the internet, and sends responses back.

--- 

## Project Setup 

### Prerequisites 
- Python 3.12+
- Docker
- Virtual environment (venv)

  
### Setup with venv
- bash
- python -m venv venv
- venv\Scripts\activate      (For Windows)
- pip install -r requirements.txt
