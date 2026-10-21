from fastapi.routing import APIRoute

from backend.main import app


def test_every_operation_has_an_id_and_a_one_line_docstring():
    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    for route in routes:
        doc = route.endpoint.__doc__ or ""
        assert route.operation_id == route.endpoint.__name__, route.path
        assert doc.strip(), route.path
        assert "\n" not in doc.strip(), route.path


def test_no_operation_has_an_optional_input():
    schema = app.openapi()
    models = schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            for parameter in operation.get("parameters", []):
                assert parameter["required"], (path, parameter["name"])
            body = operation.get("requestBody")
            if body:
                assert body["required"], path
                ref = body["content"]["application/json"]["schema"]["$ref"]
                model = models[ref.split("/")[-1]]
                assert set(model.get("required", [])) == set(model["properties"]), path
