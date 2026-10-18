from fastapi.testclient import TestClient


def test_liveness_and_documentation_work_without_a_database(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/tasks" in schema["paths"]
    response = schema["paths"]["/api/v1/tasks"]["post"]["responses"]["422"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )


def test_openapi_operation_ids_are_unique(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    operation_ids = [
        operation["operationId"]
        for path in paths.values()
        for operation in path.values()
    ]
    assert len(operation_ids) == len(set(operation_ids))
