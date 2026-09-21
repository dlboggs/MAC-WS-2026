# CREATEINSPECTIONFORM
# Automation Script — Generic Inspection Form Builder
#
# Creates a Maximo Inspection Form with any number of single-choice (Yes/No)
# questions from a pipe-delimited list.
#
# Exposed as an MCP tool so Bob can create inspection forms from a
# natural-language request in the chat UI.
#
# Input variables (all IN, LITERAL, ALN):
#   formname    — Name of the inspection form (required)
#   description — Short description of the form (required)
#   siteid      — Site ID, e.g. BEDFORD (required)
#   orgid       — Org ID, e.g. EAGLENA (required)
#   questions   — Pipe-delimited list of question texts, e.g.
#                 "Emergency stop operational?|Handrails damaged?|Debris present?"
#
# Output: responseBody (JSON string)
#
# MCP Tool Description (paste into Maximo MCP tool config):
#   Creates a Maximo Inspection Form with single-choice Yes/No questions.
#   Required inputs: formname, description, siteid, orgid, questions.
#   The questions input is a pipe-delimited list of question texts.
#   Always pass siteid as BEDFORD and orgid as EAGLENA unless the user
#   specifies otherwise. Do not ask the user for siteid or orgid.

from psdi.server import MXServer

responseBody = '{"error":"Unknown error"}'

try:
    mxServer = MXServer.getMXServer()
    userInfo = mxServer.getSystemUserInfo()

    # Parse and validate inputs
    formName    = (formname    or "").strip()
    formDesc    = (description or "").strip()
    siteId      = (siteid      or "BEDFORD").strip()
    orgId       = (orgid       or "EAGLENA").strip()
    questionsRaw = (questions  or "").strip()

    if not formName:
        responseBody = '{"error":"formname is required"}'
        raise Exception("formname is required")

    if not questionsRaw:
        responseBody = '{"error":"questions is required"}'
        raise Exception("questions is required")

    questionList = [q.strip() for q in questionsRaw.split("|") if q.strip()]

    if len(questionList) == 0:
        responseBody = '{"error":"No valid questions found in input"}'
        raise Exception("No valid questions found")

    # Delete any existing form with the same name/site to avoid duplicates
    formSet = mxServer.getMboSet("INSPECTIONFORM", userInfo)
    formSet.setWhere("name='%s' AND siteid='%s'" % (formName.replace("'", "''"), siteId))
    formSet.reset()
    existing = formSet.getMbo(0)
    if existing is not None:
        existing.delete()
        formSet.save()
        formSet.reset()

    # Create the new form
    formMbo = formSet.add()
    formMbo.setValue("NAME",        formName)
    formMbo.setValue("DESCRIPTION", formDesc if formDesc else formName)
    formMbo.setValue("ORGID",       orgId)
    formMbo.setValue("SITEID",      siteId)

    questionSet = formMbo.getMboSet("INSPQUESTION")

    for seq, qText in enumerate(questionList, start=1):
        qMbo = questionSet.add()
        qMbo.setValue("DESCRIPTION", qText)
        qMbo.setValue("SEQUENCE",    seq)
        qMbo.setValue("GROUPSEQ",    float(seq))
        qMbo.setValue("REQUIRED",    False)

        fieldSet = qMbo.getMboSet("INSPFIELD")
        fMbo = fieldSet.add()
        fMbo.setValue("FIELDTYPE",   "SO")
        fMbo.setValue("SEQUENCE",    1)
        fMbo.setValue("DESCRIPTION", qText)
        fMbo.setValue("REQUIRED",    False)
        fMbo.setValue("VISIBLE",     True)

    # Save now so Maximo assigns INSPFORMNUM, INSPQUESTIONNUM, INSPFIELDNUM
    # before we add options (INSPFIELDOPTION requires all FK keys)
    formSet.save()

    # Re-open and read the assigned form number
    formSet.setWhere("name='%s' AND siteid='%s'" % (formName.replace("'", "''"), siteId))
    formSet.reset()
    formMbo = formSet.getMbo(0)
    formNum  = formMbo.getString("INSPFORMNUM")
    questionSet = formMbo.getMboSet("INSPQUESTION")
    questionSet.reset()

    for qi in range(questionSet.count()):
        qMbo = questionSet.getMbo(qi)
        if qMbo is None:
            continue
        inspQuestionNum = qMbo.getString("INSPQUESTIONNUM")
        fieldSet = qMbo.getMboSet("INSPFIELD")
        fieldSet.reset()
        fMbo = fieldSet.getMbo(0)
        if fMbo is not None:
            inspFieldNum = fMbo.getString("INSPFIELDNUM")
            optSet = fMbo.getMboSet("INSPFIELDOPTION")

            optYes = optSet.add()
            optYes.setValue("DESCRIPTION",     "Yes")
            optYes.setValue("SEQUENCE",        1)
            optYes.setValue("REQUIREACTION",   False)
            optYes.setValue("INSPFIELDNUM",    inspFieldNum)
            optYes.setValue("INSPQUESTIONNUM", inspQuestionNum)
            optYes.setValue("INSPFORMNUM",     formNum)
            optYes.setValue("REVISION",        1)

            optNo = optSet.add()
            optNo.setValue("DESCRIPTION",     "No")
            optNo.setValue("SEQUENCE",        2)
            optNo.setValue("REQUIREACTION",   False)
            optNo.setValue("INSPFIELDNUM",    inspFieldNum)
            optNo.setValue("INSPQUESTIONNUM", inspQuestionNum)
            optNo.setValue("INSPFORMNUM",     formNum)
            optNo.setValue("REVISION",        1)

    formSet.save()

    # Read back assigned form number
    formSet.setWhere("name='%s' AND siteid='%s'" % (formName.replace("'", "''"), siteId))
    formSet.reset()
    saved   = formSet.getMbo(0)
    formNum = saved.getString("INSPFORMNUM") if saved is not None else "unknown"

    responseBody = '{"status":"created","inspformnum":"%s","name":"%s","siteid":"%s","questioncount":%d}' % (
        formNum, formName.replace('"', '\\"'), siteId, len(questionList)
    )

    formSet.close()

except Exception, e:
    if responseBody == '{"error":"Unknown error"}':
        responseBody = '{"error":"%s"}' % str(e).replace('"', '\\"')
