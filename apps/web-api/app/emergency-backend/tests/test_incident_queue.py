def test_queue_endpoint(client):
    r = client.get("/api/incidents/queue")
    assert r.status_code in (200, 204)
