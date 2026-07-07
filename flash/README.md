# GLM-OCR Flash App

Single combined KYC worker (`glm-kyc`).

```bash
export PYTHONPATH=..
flash login
flash dev --auto-provision
```

Deploy:

```bash
flash deploy
```

Call via RunPod `/runsync`:

```json
{
  "input": {
    "task": "kyc_parse",
    "image": "data:image/jpeg;base64,...",
    "document_type": "passport",
    "country": "RU"
  }
}
```
