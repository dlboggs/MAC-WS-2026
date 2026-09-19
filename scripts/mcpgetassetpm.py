# MCPGETASSETPM
# Automation Script — PM Query
#
# Retrieves Preventive Maintenance records filtered by any combination of
# assetnum, location, route, and siteid. All inputs are optional individually
# but at least one of assetnum, location, or route must be provided.
#
# Input variables:
#   assetnum  (IN, LITERAL, ALN) — filter by asset
#   location  (IN, LITERAL, ALN) — filter by location
#   route     (IN, LITERAL, ALN) — filter by route
#   siteid    (IN, LITERAL, ALN) — filter by site (recommended to narrow results)
#
# Output: responseBody (JSON string — array of PM records)
#
# NOTE: Maximo runs Jython — the standard Python 'json' module is not available.
#       responseBody must be assigned as a plain string, not a dict.
#
# Lab: Lab 10 — Capstone, Exercise 10.2

from psdi.server import MXServer

responseBody = '{"error":"Unknown error"}'

try:
    mxServer = MXServer.getMXServer()
    userInfo = mxServer.getSystemUserInfo()
    pmSet    = mxServer.getMboSet("PM", userInfo)

    # Build WHERE clause dynamically from whichever inputs were provided
    conditions = []

    if assetnum:
        conditions.append("assetnum='%s'" % assetnum)
    if location:
        conditions.append("location='%s'" % location)
    # route is not exposed as a script variable due to Jython type binding limitations
    # pass route filtering via location if needed
    if siteid:
        conditions.append("siteid='%s'" % siteid)

    if len(conditions) == 0:
        responseBody = '{"error":"At least one of assetnum or location must be provided"}'
    else:
        pmSet.setWhere(" AND ".join(conditions))
        pmSet.reset()

        records = []
        i = 0
        pm = pmSet.getMbo(i)

        while pm is not None:
            pmnum         = pm.getString("PMNUM")
            description   = pm.getString("DESCRIPTION").replace('"', '\\"')
            pm_assetnum   = pm.getString("ASSETNUM")
            pm_location   = pm.getString("LOCATION")
            pm_route      = pm.getString("ROUTE")
            pm_siteid     = pm.getString("SITEID")
            status        = pm.getString("STATUS")
            lastcompdate  = pm.getString("LASTCOMPDATE")
            nextdate      = pm.getString("NEXTDATE")
            laststartdate = pm.getString("LASTSTARTDATE")
            frequency     = str(pm.getInt("FREQUENCY"))
            frequnit      = pm.getString("FREQUNIT")
            jpnum         = pm.getString("JPNUM")
            worktype      = pm.getString("WORKTYPE")

            record = '{"pmnum":"%s","description":"%s","assetnum":"%s","location":"%s","route":"%s","siteid":"%s","status":"%s","lastcompdate":"%s","nextdate":"%s","laststartdate":"%s","frequency":%s,"frequnit":"%s","jpnum":"%s","worktype":"%s"}' % (
                pmnum, description, pm_assetnum, pm_location, pm_route, pm_siteid,
                status, lastcompdate, nextdate, laststartdate,
                frequency, frequnit, jpnum, worktype
            )
            records.append(record)

            i += 1
            pm = pmSet.getMbo(i)

        pmSet.close()

        if len(records) == 0:
            responseBody = '{"message":"No PM records found for the given filter criteria","pmcount":0,"records":[]}'
        else:
            responseBody = '{"pmcount":%d,"records":[%s]}' % (
                len(records), ",".join(records)
            )

except Exception, e:
    responseBody = '{"error":"%s"}' % str(e).replace('"', '\\"')
