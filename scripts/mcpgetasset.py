# MCPGETASSET
# Automation Script — Asset Information Query
#
# Retrieves key information about a specific asset including description,
# location, status, running state, failure class, priority, manufacturer,
# warranty expiration date, and historical maintenance costs.
#
# Input variables:
#   assetnum  (IN, LITERAL, ALN) — required
#   siteid    (IN, LITERAL, ALN) — required
#
# Output: responseBody (JSON string)
#
# NOTE: Maximo runs Jython — the standard Python 'json' module is not available.
#       responseBody must be assigned as a plain string, not a dict.
#
# Lab: Lab 10 — Capstone, Exercise 10.1

from psdi.server import MXServer

responseBody = '{"error":"Unknown error"}'

try:
    mxServer  = MXServer.getMXServer()
    userInfo  = mxServer.getSystemUserInfo()
    assetSet  = mxServer.getMboSet("ASSET", userInfo)

    assetSet.setWhere("assetnum='%s' AND siteid='%s'" % (assetnum, siteid))
    assetSet.reset()

    asset = assetSet.getMbo(0)

    if asset is None:
        responseBody = '{"error":"Asset %s not found in site %s"}' % (assetnum, siteid)
    else:
        isrunning       = "true" if asset.getBoolean("ISRUNNING") else "false"
        description     = asset.getString("DESCRIPTION").replace('"', '\\"')
        location        = asset.getString("LOCATION")
        status          = asset.getString("STATUS")
        failurecode     = asset.getString("FAILURECODE")
        priority        = asset.getString("PRIORITY")
        serialnum       = asset.getString("SERIALNUM")
        manufacturer    = asset.getString("MANUFACTURER")
        installdate     = asset.getString("INSTALLDATE")
        warrantyexpdate = asset.getString("WARRANTYEXPDATE")
        ytdcost         = str(asset.getDouble("YTDCOST"))
        totalcost       = str(asset.getDouble("TOTALCOST"))
        replacecost     = str(asset.getDouble("REPLACECOST"))

        responseBody = '{"assetnum":"%s","description":"%s","siteid":"%s","location":"%s","status":"%s","isrunning":%s,"failurecode":"%s","priority":"%s","serialnum":"%s","manufacturer":"%s","installdate":"%s","warrantyexpdate":"%s","ytdcost":%s,"totalcost":%s,"replacecost":%s}' % (
            assetnum, description, siteid, location, status, isrunning,
            failurecode, priority, serialnum, manufacturer,
            installdate, warrantyexpdate, ytdcost, totalcost, replacecost
        )

    assetSet.close()

except Exception, e:
    responseBody = '{"error":"%s"}' % str(e).replace('"', '\\"')
