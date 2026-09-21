# CREATEPM
# Automation Script — Preventive Maintenance Record Builder
#
# Creates one PM record per asset or location provided.
# Sets work type PM, WO status WMATL, frequency 1 day, next due = today.
#
# Exposed as an MCP tool so Bob can create PM records from a
# natural-language request in the chat UI.
#
# Input variables (all IN, LITERAL, ALN):
#   description  — Short description applied to every PM (required)
#   assets       — Pipe-delimited asset numbers, e.g. "11450|11230|11100"
#   locations    — Pipe-delimited location codes, e.g. "BR450|BR230"
#   jpnum        — Job Plan number to associate with every PM (optional)
#   siteid       — Site ID, e.g. BEDFORD (default: BEDFORD)
#   orgid        — Org ID, e.g. EAGLENA (default: EAGLENA)
#
# At least one of assets or locations must be provided.
# If both are provided, a PM is created for each asset AND each location.
#
# Output: responseBody (JSON string)
#
# MCP Tool Description:
#   Creates Maximo Preventive Maintenance (PM) records for one or more assets
#   or locations. Pass assets as a pipe-delimited list (e.g. "11450|11230")
#   and/or locations as a pipe-delimited list (e.g. "BR450|BR230").
#   Sets work type PM, WO status WMATL, frequency 1 day, next due date today.
#   Required: description. Optional: assets, locations, jpnum.
#   Always pass siteid=BEDFORD and orgid=EAGLENA unless the user specifies
#   otherwise. Do not ask the user for siteid or orgid.

from psdi.server import MXServer
from psdi.mbo import MboConstants

responseBody = '{"error":"Unknown error"}'

try:
    mxServer = MXServer.getMXServer()
    userInfo = mxServer.getSystemUserInfo()

    # --- Parse inputs ---
    pmDesc    = (description or "").strip()
    assetsRaw = (assets      or "").strip()
    locsRaw   = (locations   or "").strip()
    jpNum     = (jpnum       or "").strip()
    siteId    = (siteid      or "BEDFORD").strip()
    orgId     = (orgid       or "EAGLENA").strip()

    if not pmDesc:
        responseBody = '{"error":"description is required"}'
        raise Exception("description is required")

    assetList = [a.strip() for a in assetsRaw.split("|") if a.strip()] if assetsRaw else []
    locList   = [l.strip() for l in locsRaw.split("|")   if l.strip()] if locsRaw   else []

    if not assetList and not locList:
        responseBody = '{"error":"at least one asset or location is required"}'
        raise Exception("at least one asset or location is required")

    today = mxServer.getDate()
    created = []

    # --- Create one PM per asset ---
    for assetNum in assetList:
        pmSet = mxServer.getMboSet("PM", userInfo)
        pmMbo = pmSet.add()
        pmMbo.setValue("DESCRIPTION", pmDesc)
        pmMbo.setValue("ASSETNUM",    assetNum)
        pmMbo.setValue("WORKTYPE",    "PM")
        pmMbo.setValue("WOSTATUS",    "WMATL")
        pmMbo.setValue("FREQUENCY",   1)
        pmMbo.setValue("FREQUNIT",    "DAYS")
        pmMbo.setValue("NEXTDATE",    today, MboConstants.NOACCESSCHECK)
        if jpNum:
            pmMbo.setValue("JPNUM", jpNum)
        pmSet.save()
        pmNum = pmMbo.getString("PMNUM")
        created.append('{"pmnum":"%s","assetnum":"%s","location":""}' % (pmNum, assetNum))
        pmSet.close()

    # --- Create one PM per location ---
    for loc in locList:
        pmSet = mxServer.getMboSet("PM", userInfo)
        pmMbo = pmSet.add()
        pmMbo.setValue("DESCRIPTION", pmDesc)
        pmMbo.setValue("LOCATION",    loc)
        pmMbo.setValue("WORKTYPE",    "PM")
        pmMbo.setValue("WOSTATUS",    "WMATL")
        pmMbo.setValue("FREQUENCY",   1)
        pmMbo.setValue("FREQUNIT",    "DAYS")
        pmMbo.setValue("NEXTDATE",    today, MboConstants.NOACCESSCHECK)
        if jpNum:
            pmMbo.setValue("JPNUM", jpNum)
        pmSet.save()
        pmNum = pmMbo.getString("PMNUM")
        created.append('{"pmnum":"%s","assetnum":"","location":"%s"}' % (pmNum, loc))
        pmSet.close()

    responseBody = (
        '{"status":"created","count":%d,"siteid":"%s","jpnum":"%s","records":[%s]}'
    ) % (
        len(created),
        siteId,
        jpNum,
        ",".join(created)
    )

except Exception, e:
    if responseBody == '{"error":"Unknown error"}':
        responseBody = '{"error":"%s"}' % str(e).replace('"', '\\"')
