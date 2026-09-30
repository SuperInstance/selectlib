"""The one place that talks to a model, so the rest of the library stays offline.

The contract is the documented one and the control is in the test suite: `state` is a
STRING, and the option set IS the criteria keys. There is no `options` field. A malformed
spec does not error -- it returns a well-formed, confidently unhelpful answer, which is
how this project published a false claim about a model for an afternoon."""
import json, os, random, time, urllib.request, urllib.error

BASE = "https://api.typesafe.ai/v1/systemone"
KEY = os.environ.get("TYPESAFEAI_KEY", "")
MODEL = "jev-1.13.0"
CRIT = {"correct": "This cell already matches what the scene calls for; correcting it wastes compute.",
        "needs_fix": "This cell does not match what the scene calls for and should be corrected."}


def call(state, criteria, instructions, qid="q", tries=4):
    body = {"model": MODEL, "state": state,
            "questions": {qid: {"type": "choice", "instructions": instructions,
                                 "criteria": criteria}}}
    req = urllib.request.Request(BASE, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "selectlib/0.1"})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=50) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and a < tries - 1:
                time.sleep(0.5 + random.random() * 0.3); continue
            return {"error": f"HTTP {e.code}"}
        except Exception:
            if a < tries - 1:
                time.sleep(0.5); continue
            return {"error": "transport"}


def jev_judge(state):
    r = call(state, CRIT, "Does this cell already match what the scene calls for, "
                          "or does it need correcting?")
    ans = (r.get("answers") or {}).get("q")
    if not ans:
        return 0.5
    p = ans.get("probabilities") or {}
    if not p:
        return 0.5
    return float(p.get("needs_fix", 0.0))
