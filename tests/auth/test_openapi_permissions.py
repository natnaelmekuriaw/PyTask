from fastapi.testclient import TestClient


def test_versioned_operations_declare_permissions_and_denial_responses(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    schema = client.get("/openapi.json", headers=headers).json()
    scheme = schema["components"]["securitySchemes"]["APIKey"]
    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"
    for path, methods in schema["paths"].items():
        for operation in methods.values():
            if path.startswith("/api/v1/"):
                assert operation["security"] == [
                    {"APIKey": operation["x-required-scopes"]}
                ]
                assert operation["x-required-scopes"]
                assert {"401", "403"} <= operation["responses"].keys()
            else:
                assert "security" not in operation
