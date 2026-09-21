# Scenario 1 — Maintenance Planning

**IBM Bob + Maximo MCP Lab**  
**Status:** ✅ Verified end-to-end — all three MCP tools confirmed working

---

## Overview

This scenario demonstrates AI-assisted maintenance planning using IBM Bob and Maximo.
Starting from nothing, a student uses natural language to create an inspection form,
build a job plan, and schedule preventive maintenance for a fleet of escalator assets —
in three prompts.

**MCP Tools used:**

| Tool | Maximo Script | Purpose |
|---|---|---|
| `script_createinspectionform` | `CREATEINSPECTIONFORM` | Create Yes/No inspection form |
| `script_createjobplan` | `CREATEJOBPLAN` | Create job plan with tasks, crafts, materials |
| `script_createpm` | `CREATEPM` | Create PM records for one or more assets or locations |

---

## Prerequisites

- Bob is running with the Maximo MCP server configured in `.bob/mcp.json`
- All three scripts are deployed and active in Maximo Automation Scripts
- Site: **BEDFORD**, Org: **EAGLENA**

---

## Step 1 — Create the Inspection Form

### Prompt

> *"Create a daily escalator inspection form with the following questions:
> Emergency stop operational? | Handrails damaged? | Debris present? |
> Safety signage present? | Water intrusion observed?"*

### What Bob does

Bob calls `script_createinspectionform` with:

| Input | Value |
|---|---|
| `formname` | Daily Escalator Inspection |
| `description` | Daily Escalator Inspection |
| `siteid` | BEDFORD *(set automatically)* |
| `orgid` | EAGLENA *(set automatically)* |
| `questions` | Emergency stop operational?\|Handrails damaged?\|Debris present?\|Safety signage present?\|Water intrusion observed? |

### What the script creates

- **INSPECTIONFORM** record with `NAME`, `DESCRIPTION`, `SITEID`, `ORGID`
- For each question: **INSPQUESTION** with `DESCRIPTION`, `SEQUENCE`, `GROUPSEQ`, `REQUIRED=False`
- For each question: **INSPFIELD** with `FIELDTYPE=SO` (single choice), `DESCRIPTION`, `SEQUENCE`, `REQUIRED=False`, `VISIBLE=True`
- For each field: **INSPFIELDOPTION** — "Yes" (seq 1) and "No" (seq 2) with `REQUIREACTION=False`
- Form is created in **DRAFT** status

### Expected response

```json
{
  "status": "created",
  "inspformnum": "1015",
  "name": "Daily Escalator Inspection",
  "siteid": "BEDFORD",
  "questioncount": 5
}
```

### ⚠️ Manual step required

> **Activate the inspection form before proceeding.**
>
> Maximo only allows **ACTIVE** inspection forms to be linked to job plans.
> Go to: Maximo → Inspections → find the form → change status to **Active**.

---

## Step 2 — Create the Job Plan

### Prompt

> *"Create a job plan called Daily Escalator Inspection for daily escalator inspection.
> Add tasks: Visual inspection | Test emergency stop | Inspect handrails |
> Inspect comb plates | Verify safety signage.
> Add crafts: ELECT | MECH.
> Add material: Z-RAGS from the CENTRAL storeroom.
> Associate inspection form 1015."*

### What Bob does

Bob calls `script_createjobplan` with:

| Input | Value |
|---|---|
| `jpnum` | ESCL-DAILY *(≤ 12 chars)* |
| `description` | Daily Escalator Inspection |
| `siteid` | BEDFORD *(set automatically)* |
| `orgid` | EAGLENA *(set automatically)* |
| `tasks` | Visual inspection\|Test emergency stop\|Inspect handrails\|Inspect comb plates\|Verify safety signage |
| `crafts` | ELECT\|MECH |
| `materials` | Z-RAGS |
| `storeroom` | CENTRAL *(default)* |
| `inspformnum` | 1015 |

### What the script creates

**JOBPLAN** record:

| Field | Value |
|---|---|
| `JPNUM` | as provided |
| `DESCRIPTION` | as provided |
| `SITEID` | BEDFORD |
| `ORGID` | EAGLENA |
| `TEMPLATETYPE` | MAINTENANCE |

**JOBTASK** records — one per task:

| Field | Value |
|---|---|
| `JPTASK` | 10, 20, 30, 40, 50 (increments of 10) |
| `DESCRIPTION` | task text |
| `TASKDURATION` | 0.1667 hrs (10 minutes) |

**JOBLABOR** records — one per craft:

| Field | Value |
|---|---|
| `CRAFT` | ELECT, MECH |
| `LABORHRS` | 1.0 |
| `QUANTITY` | 1 |

**JOBMATERIAL** records — one per material:

| Field | Value |
|---|---|
| `ITEMNUM` | Z-RAGS |
| `ITEMQTY` | 1.0 *(default)* |
| `LOCATION` | CENTRAL |
| `LINETYPE` | ITEM |
| `STORELOCSITE` | BEDFORD |

**INSPFORMNUM** linked at job plan level (requires ACTIVE form).

> **Note:** Material quantity can be specified as `ITEMNUM:QTY` e.g. `Z-RAGS:3`.
> Multiple materials are pipe-delimited: `Z-RAGS:2|OIL-1QT:1`.

### Expected response

```json
{
  "status": "created",
  "jpnum": "ESCL-DAILY",
  "description": "Daily Escalator Inspection",
  "siteid": "BEDFORD",
  "taskcount": 5,
  "craftcount": 2,
  "materialcount": 1,
  "inspformnum": "1015"
}
```

### ⚠️ Manual step required

> **Activate the job plan before creating PMs.**
>
> Maximo requires job plans to be in **ACTIVE** status before PM records can reference them.
> Go to: Maximo → Job Plans → find the job plan → change status to **Active**.

---

## Step 3 — Create Preventive Maintenance Records

### Prompt

> *"Create PMs for the escalator assets at 11th and 12th G Street location
> using job plan ESCL-DAILY."*

### What Bob does

Bob first queries Maximo for escalator assets at 11th & G and 12th & G Street,
identifies `ESC-11G-1`, `ESC-11G-2`, `ESC-12G-1`, `ESC-12G-2`,
then calls `script_createpm` with:

| Input | Value |
|---|---|
| `description` | Daily Escalator Inspection |
| `assets` | ESC-11G-1\|ESC-11G-2\|ESC-12G-1\|ESC-12G-2 |
| `jpnum` | ESCL-DAILY |
| `siteid` | BEDFORD *(set automatically)* |
| `orgid` | EAGLENA *(set automatically)* |

### What the script creates

One **PM** record per asset:

| Field | Value |
|---|---|
| `PMNUM` | auto-assigned |
| `DESCRIPTION` | as provided |
| `ASSETNUM` | each asset in the list |
| `JPNUM` | as provided |
| `WORKTYPE` | PM |
| `WOSTATUS` | WMATL |
| `FREQUENCY` | 1 |
| `FREQUNIT` | DAYS |
| `NEXTDATE` | today (date script runs) |

> For location-based PMs instead of asset-based, use the `locations` input
> with a pipe-delimited list of location codes (e.g. `MC-ENT-11G|MC-ENT-12G`).
> Both `assets` and `locations` can be provided in the same call.

### Expected response

```json
{
  "status": "created",
  "count": 4,
  "siteid": "BEDFORD",
  "jpnum": "ESCL-DAILY",
  "records": [
    {"pmnum": "1022", "assetnum": "ESC-11G-1", "location": ""},
    {"pmnum": "1023", "assetnum": "ESC-11G-2", "location": ""},
    {"pmnum": "1024", "assetnum": "ESC-12G-1", "location": ""},
    {"pmnum": "1025", "assetnum": "ESC-12G-2", "location": ""}
  ]
}
```

---

## Reference — Escalator Assets in BEDFORD

| Asset | Description | Location |
|---|---|---|
| ESC-11G-1 | Escalator 11th & G St NW - Unit 1 (Up) | MC-ENT-11G |
| ESC-11G-2 | Escalator 11th & G St NW - Unit 2 (Down) | MC-ENT-11G |
| ESC-12G-1 | Escalator 12th & G St NW - Unit 1 (Up) | MC-ENT-12G |
| ESC-12G-2 | Escalator 12th & G St NW - Unit 2 (Down) | MC-ENT-12G |
| ESC-12F-1 | Escalator 12th & F St NW - Unit 1 (Up) | MC-ENT-12F |
| ESC-12F-2 | Escalator 12th & F St NW - Unit 2 (Down) | MC-ENT-12F |
| ESC-13G-1 | Escalator 13th & G St NW - Unit 1 (Up) | MC-ENT-13G |
| ESC-13G-2 | Escalator 13th & G St NW - Unit 2 (Down) | MC-ENT-13G |
| ESC-LM-LL-1 | Escalator Lower Mezz to Lower Platform - Unit 1 | MC-LMEZZ |
| ESC-LM-LL-2 | Escalator Lower Mezz to Lower Platform - Unit 2 | MC-LMEZZ |
| ESC-UM-LM-1 | Escalator Upper Mezz to Lower Mezz - Unit 1 | MC-UMEZZ |
| ESC-UM-RL-1 | Escalator Upper Mezz to Red Line - Unit 1 | MC-UMEZZ |
| ESC-UM-RL-2 | Escalator Upper Mezz to Red Line - Unit 2 | MC-UMEZZ |

---

## Known Issues & Workarounds

| # | Issue | Workaround |
|---|---|---|
| 15 | Inspection form must be manually activated before linking to a job plan | Activate in Maximo UI: Inspections → form → change status to Active |
| 16 | Job plan must be manually activated before PM records can be created | Activate in Maximo UI: Job Plans → plan → change status to Active |
| — | `inspformnum` MCP input treated as integer by MCP server when a numeric value is passed | Link inspection form to job plan manually in the UI, or pass a non-numeric form name |
| — | `JPNUM` max length is 12 characters | Keep job plan IDs ≤ 12 chars (e.g. `ESCL-DAILY` not `JP-ESCL-DAILY`) |
| — | Script source field not writable via REST PATCH on `mxapiautoscript` | Update script source directly in Maximo UI Automation Scripts editor |
