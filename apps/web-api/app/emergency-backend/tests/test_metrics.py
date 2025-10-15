def test_metrics_tiles(client):
    r = client.get("/api/metrics/tiles")
    assert r.status_code == 200
