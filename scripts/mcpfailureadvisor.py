# MCPFAILUREADVISOR
# Automation Script — Inspection Failure Advisor
#
# Evaluates an inspection finding and returns severity, priority,
# responsible craft, and recommended corrective action.
#
# Input variable:  finding  (IN, LITERAL, ALN)
# Output:          responseBody (JSON string)
#
# NOTE: Maximo runs Jython — the standard Python 'json' module is not available.
#       responseBody must be assigned as a plain string, not a dict.
#
# Lab: Lab 09 — Creating an Automation Script MCP Tool

severity    = "LOW"
priority    = 4
craft       = "OPERATIONS"
action      = "Monitor"
matchedRule = "DEFAULT"

if finding:
    text = finding.strip().lower()

    if "emergency stop" in text:
        severity    = "CRITICAL"
        priority    = 1
        craft       = "ELECTRICAL"
        action      = "Create corrective work order"
        matchedRule = "EMERGENCY_STOP"

    elif "fire extinguisher" in text:
        severity    = "HIGH"
        priority    = 2
        craft       = "SAFETY"
        action      = "Replace immediately"
        matchedRule = "FIRE_EXTINGUISHER"

    elif "water intrusion" in text:
        severity    = "HIGH"
        priority    = 2
        craft       = "FACILITIES"
        action      = "Inspect electrical equipment"
        matchedRule = "WATER_INTRUSION"

    elif "trip hazard" in text:
        severity    = "MEDIUM"
        priority    = 3
        craft       = "FACILITIES"
        action      = "Repair within 24 hours"
        matchedRule = "TRIP_HAZARD"

    elif "grinding" in text:
        severity    = "MEDIUM"
        priority    = 2
        craft       = "MECHANICAL"
        action      = "Create corrective work order"
        matchedRule = "GRINDING_NOISE"

responseBody = '{"severity":"%s","priority":%d,"craft":"%s","recommendedAction":"%s","matchedRule":"%s"}' % (
    severity, priority, craft, action, matchedRule
)
