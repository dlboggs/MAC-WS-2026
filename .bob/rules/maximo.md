# Maximo Configuration

## Decision Order for ALL Maximo Operations
1. **Check for an MCP tool first** — always look for a `mcp__maximoinst1__*` tool before writing any REST API call
2. **If no MCP tool exists, use REST API** — but always call `apischema` first to confirm field names before constructing the payload. Never guess field names.
3. **Never use REST when an MCP tool is available** — MCP tools are cheaper, safer, and don't require field name knowledge


## Part 1 — REST API (Used in Early Exercises)

When the user asks you to interact with IBM Maximo and the MCP service is not available, use
direct REST API calls with the following settings.

**Base Maximo URL:**
```
Remove this url https://gtmexpertlab-all.manage.masexpertlab.apps.itz-bpufg7.infra01-lb.wdc04.techzone.ibm.com/
Replace with your BASE Maximo URL, when done only the url remains between the ''' and '''
```

**Authentication** — include this on every API call:
```
?apikey=APIKEY_HERE
```

**API Path** — always use this format (not the older OSLC path):
```
/maximo/api/os/<object-structure>
```
**Querying / Filtering records** — the REST API uses `oslc.where` and `oslc.select` as query parameters (this is normal for the Maximo REST API, not the old OSLC path). Always use `--data-urlencode` with `-G` in curl to avoid encoding issues:
```bash
curl -k -s -G "<base_url>/maximo/api/os/mxapiasset" \
  --data-urlencode "apikey=<key>" \
  --data-urlencode 'oslc.where=assetnum="ESC-12G-1"' \
  --data-urlencode 'oslc.select=assetnum,description,status,location,siteid'
```
- Plain `?where=` parameters are silently ignored — always use `oslc.where`
- Response fields are returned with the `spi:` prefix (e.g. `spi:description`, `spi:status`)

**Location Hierarchy** — locations are hierarchical. To find all assets at a site or station, first query `mxapilocation` with `parent="<location>"` to discover child location codes, then query assets by each child location. Never guess location codes. Example:
```
oslc.where=siteid="BEDFORD" and parent="MC"  → returns MC-STR, MC-UMEZZ, MC-LMEZZ, etc.
```

**Check schemas first** — before querying or filtering on a new object structure, use the `apischema` MCP tool to both confirm the object structure name exists AND understand its available fields. Never guess object structure names with trial curl calls — one `apischema` call is cheaper. Known valid object structures:
- `mxapisr` — Service Requests
- `mxapiwodetail` — Work Orders
- `mxapiasset` — Assets
- `mxapilocation` — Locations
- `mxapijobplan` — Job Plans (tasks in `/jobtask` collection, materials in `/jobmaterial` collection)

**Field Naming** — always use the `spi:` namespace prefix on ALL field names in POST and PATCH bodies, for every object structure (not just `mxapiwodetail`). Plain field names without the prefix will be silently ignored and the record will be created empty.

**Confirm before acting** — before creating or updating any record, confirm the key details with the user in plain language. One confirmation is cheaper than fixing a mistake.

**Prompt for intent** — before every action (not just creates), ask what the user is trying to accomplish. A student asking "list all escalators at Metro Center" may actually need to create SRs or WOs for all of them. Understanding intent first prevents doing the wrong thing efficiently.

**Do not over-verify** — a HTTP 201 response means success. Do not GET the record back just to confirm — that wastes tokens.

**SSL** — this environment uses a self-signed certificate; always include the `-k` flag in curl.
**Asset Status Values** — valid statuses for Assets:
- `NOT READY` — default, not yet operational
- `OPERATING` — active and in service
- `DECOMMISSIONED` — retired from service

**SR Status Values** — valid statuses for Service Requests:
- `NEW` — newly created
- `QUEUED` — queued for assignment
- `PENDING` — pending further information
- `INPROG` — in progress
- `RESOLVED` — resolved
- `CLOSED` — closed
- `CANCELLED` — cancelled

**Creating a Service Request:**
- Send a `POST` request to `/maximo/api/os/mxapisr`
- Required fields: `description` and `assetnum` — use plain field names (no `spi:` prefix)
- A successful response is HTTP 201
- The new SR number is in the `spi:ticketid` field, retrieved from the URL in the `location` response header

**Creating a Work Order:**
- Send a `POST` request to `/maximo/api/os/mxapiwodetail`
- `mxapiwodetail` requires the `spi:` namespace prefix on all field names in the POST body
- Always include `spi:siteid` = `BEDFORD` — do not ask the user for this value
- Example payload:
```json
{
  "spi:description": "...",
  "spi:assetnum": "11450",
  "spi:siteid": "BEDFORD",
  "spi:wopriority": 1
}
```
- A successful response is HTTP 201
- The new WO number is in the `spi:wonum` field, retrievable from the URL in the `location` response header

---

## Part 2 — MCP Service (Used in Later Exercises)

When the user asks you to interact with IBM Maximo and the MCP service is available, prefer
using the MCP tools over direct REST API calls.

**MCP Endpoint URL:**
```
https://gtmexpertlab-mcp.manage.masexpertlab.apps.itz-bpufg7.infra01-lb.wdc04.techzone.ibm.com/mcp
Replace with your BASE Maximo URL, when done only the url remains between the ''' and '''
```

**Authentication** — the MCP service uses an API key passed as a request header:
```
apikey: Maximo APIKEY HERE
```

## Work Order Creation — Site

When creating a Work Order via the `os_mxapiwodetail-createworkorder` MCP tool or via
direct REST API, always include `siteid` = `BEDFORD` in the request. Do not ask the user
for the site — always use `BEDFORD` silently.

---

## Inspection Failure Advisor — Finding Classification


