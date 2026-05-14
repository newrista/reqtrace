# reqtrace

Lightweight HTTP request logger and inspector that proxies traffic and generates structured OpenAPI-compatible reports.

---

## Installation

```bash
pip install reqtrace
```

Or install from source:

```bash
git clone https://github.com/yourname/reqtrace.git && cd reqtrace && pip install -e .
```

---

## Usage

Start the proxy on a local port and point your HTTP client at it:

```bash
reqtrace start --port 8080 --target https://api.example.com
```

All traffic is intercepted and logged. Once done, export a structured report:

```bash
reqtrace report --format openapi --output report.json
```

You can also use it programmatically:

```python
from reqtrace import Proxy

proxy = Proxy(port=8080, target="https://api.example.com")
proxy.start()

# ... make your requests ...

proxy.stop()
proxy.export("report.json", format="openapi")
```

---

## Features

- Transparent HTTP/HTTPS proxy with minimal setup
- Captures request/response headers, bodies, and timing
- Generates OpenAPI 3.0-compatible path reports
- Supports JSON and YAML output formats
- Zero external dependencies beyond the standard library

---

## License

This project is licensed under the [MIT License](LICENSE).