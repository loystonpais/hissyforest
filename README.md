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


>>> r.post(url, json={"code": "print('Hello')"}).json()
{'stdout': 'Hello\n', 'stderr': '', 'exit_code': 0, 'files': {}}
>>> r.post(url, json={"code": "print('Hello'); import os; os.system('echo foo >> lol')"}).json()
{'stdout': 'Hello\n', 'stderr': '', 'exit_code': 0, 'files': {'lol': 'Zm9vCg=='}}
>>> r.post(url, json={"code": "print('Hello'); syntaxerr;'"}).json()
{'stdout': '', 'stderr': '  File "/tmp/tmpbam910xx/script.py", line 1\n    print(\'Hello\'); syntaxerr;\'\n                              ^\nSyntaxError: unterminated string literal (detected at line 1)\n', 'exit_code': 1, 'files': {}}
>>>
```
