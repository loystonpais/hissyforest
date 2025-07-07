# HissyForest

HissyForest is a simple python compiler running on AWS Lambda. Hence the name.

## Installation

Create a lambda function with python3.12 and upload the zip file provided in releases.

## Usage Example

```py
import requests as r

url = "https://xxxxxx.lambda-url.ap-south-1.on.aws/"
result = r.post(url, json={"code": "print('Hi')"}).json()

print(result)

# Example result

{
    "statusCode": int,
    "body": {
        "error": str,
        "stdout": str,
        "stderr": str,
        "exit_code": int,
        "files": {str: str} # Map of filename and content in base64
    }
}
```
