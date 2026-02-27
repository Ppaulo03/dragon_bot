from fastapi import Request
from ..schemas import TriggerRule, TriggerParams
from uuid import uuid4


class RuleFormParser:
    async def __call__(self, request: Request):
        form_data = await request.form()
        rule_ids = form_data.getlist("rule_id")

        rules = []
        for r_id in rule_ids:
            new_uploads = [
                f for f in form_data.getlist(f"file_upload_{r_id}") if f.filename
            ]
            trig_up = form_data.get(f"trigger_file_upload_{r_id}")

            rules.append(
                TriggerRule(
                    id=uuid4().hex[:8],
                    name=form_data.get(f"name_{r_id}"),
                    type=form_data.get(f"type_{r_id}"),
                    matcher=form_data.get(f"matcher_{r_id}") or "always",
                    chance=float(form_data.get(f"chance_{r_id}", 1.0)),
                    params=TriggerParams(
                        pattern=form_data.get(f"pattern_{r_id}"),
                        hash=form_data.get(f"hash_{r_id}"),
                    ),
                    action=form_data.get(f"action_{r_id}"),
                    value=form_data.get(f"value_{r_id}"),
                    existing_files=form_data.getlist(f"keep_files_{r_id}"),
                    new_files=new_uploads,
                    trigger_upload=trig_up if trig_up and trig_up.filename else None,
                )
            )
        return rules
