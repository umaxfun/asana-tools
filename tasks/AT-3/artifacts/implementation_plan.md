# AT-3: Fix init command 400 Bad Request

## Goal Description
The `init` command fails with a `400 Bad Request` when fetching projects using `GET /workspaces/{gid}/projects` with `opt_fields`. This endpoint might have limitations or issues with certain fields.
The goal is to switch to the standard `GET /projects` endpoint, which supports filtering by workspace and archived status directly.

## User Review Required
> [!NOTE]
> This change modifies how projects are fetched from Asana. It switches from `GET /workspaces/{id}/projects` to `GET /projects?workspace={id}`. This is generally the recommended approach.

## Proposed Changes

### `aa` Package

#### [MODIFY] [asana_client.py](file:///Users/umaxfun/prj/asana-tools/aa/core/asana_client.py)
- Update `get_projects` method:
    - Change endpoint from `/workspaces/{workspace_id}/projects` to `/projects`.
    - Add `workspace={workspace_id}` to params.
    - Add `archived=false` to params (server-side filtering).
    - Remove client-side filtering of archived projects.
    - Update `opt_fields` to `gid,name` (since we filter `archived=false`, we assume they are active, but we can keep `archived` if we want to be double sure, though server-side filter is better).

## Verification Plan

### Automated Tests
- Since I cannot run tests against real Asana without a token, I will verify the code changes by reviewing them.
- I will create a mock test in `tasks/AT-3/artifacts/test_client.py` that mocks `httpx.AsyncClient` and verifies that `get_projects` calls the correct URL with correct parameters.

### Manual Verification
- The user will need to run `uvx aa-cli@latest init` (or `uv run aa init` if running from source) to verify the fix.
