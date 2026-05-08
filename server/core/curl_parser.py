import shlex
import json


def parse_curl(curl_command: str) -> dict:
    curl_command = curl_command.strip()
    if curl_command.startswith("curl "):
        curl_command = curl_command[5:]
    elif curl_command == "curl":
        raise ValueError("Empty curl command")

    try:
        tokens = shlex.split(curl_command)
    except ValueError as e:
        raise ValueError(f"Invalid curl command: {e}")

    result = {
        "method": "GET",
        "url": "",
        "headers": [],
        "query_params": [],
        "body_type": "none",
        "body_raw_content": "",
        "body_form": [],
        "auth_type": "none",
        "auth": None,
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ("-X", "--request") and i + 1 < len(tokens):
            result["method"] = tokens[i + 1].upper()
            i += 2

        elif token in ("-H", "--header") and i + 1 < len(tokens):
            header_str = tokens[i + 1]
            if ":" in header_str:
                key, value = header_str.split(":", 1)
                result["headers"].append({
                    "enabled": True,
                    "key": key.strip(),
                    "value": value.strip(),
                    "description": ""
                })
            i += 2

        elif token in ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode") and i + 1 < len(tokens):
            data = tokens[i + 1]
            if result["method"] == "GET":
                result["method"] = "POST"

            try:
                json.loads(data)
                result["body_type"] = "raw-json"
                result["body_raw_content"] = data
            except json.JSONDecodeError:
                if "=" in data and "&" in data or (data.count("=") >= 1 and "{" not in data):
                    result["body_type"] = "x-www-form-urlencoded"
                    for pair in data.split("&"):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            result["body_form"].append({
                                "enabled": True,
                                "key": k,
                                "value": v,
                                "param_type": "text",
                                "description": ""
                            })
                else:
                    result["body_type"] = "raw-text"
                    result["body_raw_content"] = data
            i += 2

        elif token in ("-u", "--user") and i + 1 < len(tokens):
            user_pass = tokens[i + 1]
            if ":" in user_pass:
                username, password = user_pass.split(":", 1)
                result["auth_type"] = "basic"
                result["auth"] = {
                    "auth_type": "basic",
                    "username": username,
                    "password": password,
                }
            i += 2

        elif token == "--url" and i + 1 < len(tokens):
            result["url"] = tokens[i + 1]
            i += 2

        elif token.startswith("-"):
            i += 1

        elif not result["url"]:
            result["url"] = token
            i += 1

        else:
            i += 1

    for header in result["headers"]:
        if header["key"].lower() == "authorization":
            value = header["value"]
            if value.startswith("Bearer "):
                result["auth_type"] = "bearer"
                result["auth"] = {
                    "auth_type": "bearer",
                    "token": value[7:],
                }
            elif value.startswith("Basic "):
                import base64
                try:
                    decoded = base64.b64decode(value[6:]).decode("utf-8")
                    if ":" in decoded:
                        username, password = decoded.split(":", 1)
                        result["auth_type"] = "basic"
                        result["auth"] = {
                            "auth_type": "basic",
                            "username": username,
                            "password": password,
                        }
                except Exception:
                    pass

    if not result["url"]:
        raise ValueError("No URL found in curl command")

    if result["url"].startswith(("http://", "https://")):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(result["url"])
        if parsed.query:
            for key, values in parse_qs(parsed.query).items():
                for value in values:
                    result["query_params"].append({
                        "enabled": True,
                        "key": key,
                        "value": value,
                        "description": ""
                    })

    return result
