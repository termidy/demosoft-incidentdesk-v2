# Mobile API

The mobile API is available under `/mobile/v1`. It returns JSON.

## List incidents

`GET /mobile/v1/incidents`

Optional query parameter:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `page` | integer (minimum 1) | `1` | Page number; each page contains up to 20 incidents. |

Resolved incidents are excluded. Results are ordered by `opened_at` descending, then incident ID descending. `next_page` is the next page number when more results are available, or `null` otherwise.

Each item has `key`, `title`, `service` (service slug), `priority`, `status`, and `opened_at` (ISO 8601 timestamp).

Example response:

```json
{
  "items": [
    {
      "key": "INC-4801",
      "title": "Login fails for some customers",
      "service": "login-service",
      "priority": "P1",
      "status": "acknowledged",
      "opened_at": "2026-10-13T19:00:00Z"
    }
  ],
  "next_page": null
}
```

Proven by: `tests/api/test_mobile_incidents.py::test_mobile_list_matches_response_example`

An invalid `page` value, including a value less than 1, returns `422`.

## Get incident details

`GET /mobile/v1/incidents/{key}`

Replace `{key}` with the incident key. The response includes the incident fields returned by the list endpoint and a `timeline` array. Each timeline event has `at`, `kind`, and `note`; events are ordered oldest first.

Example response:

```json
{
  "key": "INC-4821",
  "title": "Login fails for some customers",
  "service": "login-service",
  "priority": "P1",
  "status": "acknowledged",
  "opened_at": "2026-10-13T19:00:00Z",
  "timeline": [
    {
      "at": "2026-10-13T19:00:00Z",
      "kind": "opened",
      "note": ""
    },
    {
      "at": "2026-10-13T19:01:00Z",
      "kind": "acknowledged",
      "note": ""
    }
  ]
}
```

Proven by: `tests/api/test_mobile_incident_detail.py::test_mobile_incident_detail_includes_timeline_oldest_first`

An unknown key returns `404`:

```json
{"error": "not_found"}
```

Proven by: `tests/api/test_mobile_incident_detail.py::test_mobile_incident_detail_returns_not_found`

## Create an alert subscription

`POST /mobile/v1/subscriptions`

Send a JSON body with:

| Field | Type | Description |
| --- | --- | --- |
| `engineer` | string | Engineer identifier. |
| `services` | array of strings | Service slugs to subscribe to; each slug must exist. |
| `min_priority` | string | Minimum priority: `P1`, `P2`, `P3`, or `P4`. |

Example request:

```json
{
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

Proven by: `tests/api/test_mobile_alerts.py::test_create_and_list_subscriptions`

The successful response has status `201` and contains the generated `id` and the submitted fields:

```json
{
  "id": 1,
  "engineer": "a.reyes",
  "services": ["login-service"],
  "min_priority": "P2"
}
```

Proven by: `tests/api/test_mobile_alerts.py::test_create_and_list_subscriptions`

An unknown service returns `422`. Missing required fields or a `min_priority` outside the allowed values also fail validation with `422`.

Proven by: `tests/api/test_mobile_alerts.py::test_unknown_service_is_refused`

## List an engineer's alert subscriptions

`GET /mobile/v1/subscriptions`

Required query parameter:

| Name | Type | Description |
| --- | --- | --- |
| `engineer` | string | Return subscriptions for this engineer identifier. |

The response is an array of subscription objects with `id`, `engineer`, `services`, and `min_priority`. An engineer with no subscriptions receives an empty array.

Example response:

```json
[
  {
    "id": 1,
    "engineer": "a.reyes",
    "services": ["login-service"],
    "min_priority": "P2"
  }
]
```

Proven by: `tests/api/test_mobile_alerts.py::test_create_and_list_subscriptions`

Omitting the required `engineer` query parameter returns `422`.
