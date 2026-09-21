# CREATEJOBPLAN
# Automation Script — Job Plan Builder
#
# Creates a Maximo Job Plan (template type: MAINTENANCE) with tasks, crafts,
# planned materials, and an optional linked inspection form.
#
# Exposed as an MCP tool so Bob can create job plans from a natural-language
# request in the chat UI.
#
# Input variables (all IN, LITERAL, ALN):
#   jpnum        — Job Plan number/ID (required)
#   description  — Short description of the job plan (required)
#   siteid       — Site ID, e.g. BEDFORD (required)
#   orgid        — Org ID, e.g. EAGLENA (required)
#   tasks        — Pipe-delimited task descriptions, e.g.
#                  "Inspect motor bearings|Lubricate shaft|Test operation"
#                  Each task defaults to 10 minutes (0.1667 hrs) duration.
#   crafts       — Pipe-delimited craft codes needed, e.g. "ELECT|MECH"
#                  Each craft defaults to 1 hour of labor.
#   materials    — Pipe-delimited item numbers from the storeroom, e.g.
#                  "1092-1|1093-2" (item|qty, qty optional, defaults to 1)
#                  Default storeroom is CENTRAL.
#   storeroom    — Storeroom location for materials (default: CENTRAL)
#   inspformnum  — Inspection Form number to link to the job plan (optional)
#
# Output: responseBody (JSON string)
#
# MCP Tool Description:
#   Creates a Maximo Job Plan of template type MAINTENANCE with tasks, crafts,
#   planned materials, and an optional linked inspection form.
#   Required inputs: jpnum, description, siteid, orgid.
#   Optional: tasks (pipe-delimited), crafts (pipe-delimited),
#   materials (pipe-delimited as item or item|qty), storeroom, inspformnum.
#   Always pass siteid=BEDFORD and orgid=EAGLENA unless the user specifies
#   otherwise. Default task duration is 10 minutes. Default craft hours is
#   1 hour. Default storeroom is CENTRAL.

from psdi.server import MXServer

TASK_DURATION_HRS = 0.1667   # 10 minutes
CRAFT_HOURS       = 1.0
DEFAULT_STOREROOM = "CENTRAL"

responseBody = '{"error":"Unknown error"}'

try:
    mxServer = MXServer.getMXServer()
    userInfo = mxServer.getSystemUserInfo()

    # --- Parse inputs ---
    jpNum        = (jpnum        or "").strip().upper()
    jpDesc       = (description  or "").strip()
    siteId       = (siteid       or "BEDFORD").strip()
    orgId        = (orgid        or "EAGLENA").strip()
    tasksRaw     = (tasks        or "").strip()
    craftsRaw    = (crafts       or "").strip()
    materialsRaw = (materials    or "").strip()
    storeLoc     = (storeroom    or DEFAULT_STOREROOM).strip()
    inspForm     = (inspformnum  or "").strip()

    if not jpNum:
        responseBody = '{"error":"jpnum is required"}'
        raise Exception("jpnum is required")
    if not jpDesc:
        responseBody = '{"error":"description is required"}'
        raise Exception("description is required")

    taskList = [t.strip() for t in tasksRaw.split("|") if t.strip()] if tasksRaw else []
    craftList = [c.strip().upper() for c in craftsRaw.split("|") if c.strip()] if craftsRaw else []

    # Materials: each entry is "ITEMNUM" or "ITEMNUM|QTY"
    materialList = []
    if materialsRaw:
        for m in materialsRaw.split("|"):
            parts = m.strip().split(":")
            itemNum = parts[0].strip().upper()
            qty = 1.0
            if len(parts) > 1:
                try:
                    qty = float(parts[1].strip())
                except Exception:
                    qty = 1.0
            if itemNum:
                materialList.append((itemNum, qty))

    # --- Delete existing job plan with same jpnum/site ---
    jpSet = mxServer.getMboSet("JOBPLAN", userInfo)
    jpSet.setWhere("jpnum='%s' AND siteid='%s'" % (jpNum.replace("'","''"), siteId))
    jpSet.reset()
    existing = jpSet.getMbo(0)
    if existing is not None:
        existing.delete()
        jpSet.save()
        jpSet.reset()

    # --- Create the job plan ---
    jpMbo = jpSet.add()
    jpMbo.setValue("JPNUM",        jpNum)
    jpMbo.setValue("DESCRIPTION",  jpDesc)
    jpMbo.setValue("SITEID",       siteId)
    jpMbo.setValue("ORGID",        orgId)
    jpMbo.setValue("TEMPLATETYPE", "MAINTENANCE")

    # Link inspection form at job plan level if provided
    if inspForm:
        jpMbo.setValue("INSPFORMNUM", inspForm)

    # --- Tasks ---
    taskSeq = 10
    taskSet = jpMbo.getMboSet("JOBTASK")
    for tDesc in taskList:
        tMbo = taskSet.add()
        tMbo.setValue("JPTASK",       taskSeq)
        tMbo.setValue("DESCRIPTION",  tDesc)
        tMbo.setValue("TASKDURATION", TASK_DURATION_HRS)
        taskSeq += 10

    # --- Crafts (JOBLABOR) ---
    laborSet = jpMbo.getMboSet("JOBLABOR")
    for craftCode in craftList:
        lMbo = laborSet.add()
        lMbo.setValue("CRAFT",    craftCode)
        lMbo.setValue("LABORHRS", CRAFT_HOURS)
        lMbo.setValue("QUANTITY", 1)

    # --- Planned materials (JOBMATERIAL) ---
    matSet = jpMbo.getMboSet("JOBMATERIAL")
    for itemNum, qty in materialList:
        mMbo = matSet.add()
        mMbo.setValue("ITEMNUM",      itemNum)
        mMbo.setValue("ITEMQTY",      qty)
        mMbo.setValue("LOCATION",     storeLoc)
        mMbo.setValue("LINETYPE",     "ITEM")
        mMbo.setValue("STORELOCSITE", siteId)

    jpSet.save()

    # --- Read back assigned jpnum ---
    jpSet.setWhere("jpnum='%s' AND siteid='%s'" % (jpNum.replace("'","''"), siteId))
    jpSet.reset()
    saved = jpSet.getMbo(0)
    savedNum = saved.getString("JPNUM") if saved is not None else jpNum

    responseBody = (
        '{"status":"created",'
        '"jpnum":"%s",'
        '"description":"%s",'
        '"siteid":"%s",'
        '"taskcount":%d,'
        '"craftcount":%d,'
        '"materialcount":%d,'
        '"inspformnum":"%s"}'
    ) % (
        savedNum,
        jpDesc.replace('"', '\\"'),
        siteId,
        len(taskList),
        len(craftList),
        len(materialList),
        inspForm
    )

    jpSet.close()

except Exception, e:
    if responseBody == '{"error":"Unknown error"}':
        responseBody = '{"error":"%s"}' % str(e).replace('"', '\\"')
